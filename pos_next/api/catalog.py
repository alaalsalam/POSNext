"""Flag-controlled, profile-scoped catalog management APIs."""

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

from pos_next.api.management_scope import assert_doc_permission, require_feature_permission
from pos_next.api.company_scope import OWNERSHIP_FIELD, is_multi_company_site


def _context(pos_profile=None):
	return require_feature_permission("catalog", "Item", "read", pos_profile=pos_profile)


def _allowed_item_groups(pos_profile):
	configured = frappe.get_all("POS Item Group", filters={"parent": pos_profile}, pluck="item_group", limit=0)
	return set(configured)


def _assert_item_group(name, pos_profile, *, parent=False):
	doc = assert_doc_permission("Item Group", name)
	if parent and not doc.is_group:
		frappe.throw(_("The parent Item Group must be a group"))
	if not parent and doc.is_group:
		frappe.throw(_("Items must use a leaf Item Group"))
	allowed = _allowed_item_groups(pos_profile)
	if allowed and name not in allowed:
		ancestors = set(frappe.get_all("Item Group", filters={"lft": ["<", doc.lft], "rgt": [">", doc.rgt]}, pluck="name"))
		descendants = set(frappe.get_all("Item Group", filters={"lft": [">", doc.lft], "rgt": ["<", doc.rgt]}, pluck="name"))
		if not allowed.intersection(ancestors | descendants):
			frappe.throw(_("The Item Group is outside this POS Profile"), frappe.PermissionError)
	return doc


def _price_list(name, expected_type):
	doc = assert_doc_permission("Price List", name)
	if not doc.enabled or not doc.get(expected_type):
		frappe.throw(_("The selected Price List is not enabled for {0}").format(_(expected_type)))
	return doc


def _catalog_price_lists(pos_profile, company):
	selling = frappe.db.get_value("POS Profile", pos_profile, "selling_price_list")
	buying = frappe.db.get_single_value("Buying Settings", "buying_price_list")
	if not selling or not buying:
		frappe.throw(_("Selling and buying price lists must be configured"))
	return _price_list(selling, "selling"), _price_list(buying, "buying")


def _assert_uom(uom):
	doc = assert_doc_permission("UOM", uom)
	if not doc.enabled:
		frappe.throw(_("The selected UOM is disabled"))
	return doc


def _assert_barcode_unique(barcode, item_code=None):
	if not barcode:
		return
	existing = frappe.db.get_value("Item Barcode", {"barcode": barcode}, "parent")
	if existing and existing != item_code:
		frappe.throw(_("Barcode {0} is already assigned to item {1}").format(barcode, existing))


@frappe.whitelist()
def check_catalog_permission(pos_profile=None):
	profile, company = _context(pos_profile)
	return {
		"can_manage": bool(frappe.has_permission("Item", "create")),
		"pos_profile": profile,
		"company": company,
	}


@frappe.whitelist()
def get_catalog_defaults(pos_profile=None):
	profile, company = _context(pos_profile)
	selling, buying = _catalog_price_lists(profile, company)
	uoms = frappe.get_list("UOM", filters={"enabled": 1}, fields=["name"], order_by="name", limit=200)
	return {
		"pos_profile": profile,
		"company": company,
		"selling_price_list": selling.name,
		"selling_currency": selling.currency,
		"buying_price_list": buying.name,
		"buying_currency": buying.currency,
		"uoms": [row.name for row in uoms],
	}


@frappe.whitelist()
def create_quick_item(
	item_name,
	item_group,
	item_code=None,
	price=0,
	buying_price=0,
	stock_uom="Nos",
	is_stock_item=1,
	barcode=None,
	valid_from=None,
	valid_upto=None,
	opening_qty=0,
	warehouse=None,
	pos_profile=None,
):
	"""Create an Item and its profile-authorized selling/buying prices atomically."""
	profile, company = _context(pos_profile)
	frappe.has_permission("Item", "create", throw=True)
	if not (item_name or "").strip():
		frappe.throw(_("Item Name is required"))
	item_code = (item_code or item_name).strip()
	if not item_code:
		frappe.throw(_("Item Code is required"))
	if frappe.db.exists("Item", item_code):
		frappe.throw(_("Item '{0}' already exists").format(item_code))
	if flt(opening_qty) or warehouse:
		frappe.throw(_("Opening stock is not supported here; use a standard stock transaction"))
	_assert_item_group(item_group, profile)
	_assert_uom(stock_uom)
	_assert_barcode_unique(barcode)
	selling_list, buying_list = _catalog_price_lists(profile, company)
	if valid_from and valid_upto and getdate(valid_upto) < getdate(valid_from):
		frappe.throw(_("Valid Until cannot be before Valid From"))

	frappe.db.savepoint("posnext_catalog_item")
	try:
		item_data = {
			"doctype": "Item",
			"item_code": item_code,
			"item_name": item_name.strip(),
			"item_group": item_group,
			"stock_uom": stock_uom,
			"is_sales_item": 1,
			"is_purchase_item": 1,
			"is_stock_item": 1 if int(is_stock_item or 0) else 0,
			"barcodes": [{"barcode": barcode}] if barcode else [],
		}
		if is_multi_company_site() and frappe.db.has_column("Item", OWNERSHIP_FIELD):
			item_data[OWNERSHIP_FIELD] = company
		doc = frappe.get_doc(item_data).insert(ignore_permissions=False)
		if flt(price) > 0:
			_upsert_item_price(doc.name, selling_list, flt(price), stock_uom, valid_from, valid_upto)
		if flt(buying_price) > 0:
			_upsert_item_price(doc.name, buying_list, flt(buying_price), stock_uom, valid_from, valid_upto)
		return {"item_code": doc.name, "item_name": doc.item_name, "item_group": doc.item_group}
	except Exception:
		frappe.db.rollback(save_point="posnext_catalog_item")
		raise


@frappe.whitelist()
def create_item_group(group_name, parent_item_group="All Item Groups", pos_profile=None):
	profile, company = _context(pos_profile)
	frappe.has_permission("Item Group", "create", throw=True)
	group_name = (group_name or "").strip()
	if not group_name:
		frappe.throw(_("Group Name is required"))
	if frappe.db.exists("Item Group", group_name):
		frappe.throw(_("Item Group '{0}' already exists").format(group_name))
	parent = parent_item_group or "All Item Groups"
	_assert_item_group(parent, profile, parent=True)
	group_data = {
		"doctype": "Item Group",
		"item_group_name": group_name,
		"parent_item_group": parent,
		"is_group": 0,
	}
	if is_multi_company_site() and frappe.db.has_column("Item Group", OWNERSHIP_FIELD):
		group_data[OWNERSHIP_FIELD] = company
	doc = frappe.get_doc(group_data).insert(ignore_permissions=False)
	if _allowed_item_groups(profile):
		profile_doc = assert_doc_permission("POS Profile", profile, "write")
		if not any(row.item_group == doc.name for row in profile_doc.item_groups):
			profile_doc.append("item_groups", {"item_group": doc.name})
			profile_doc.save(ignore_permissions=False)
	return {"name": doc.name, "parent": doc.parent_item_group}


@frappe.whitelist()
def get_item_groups_for_select(pos_profile=None, include_parents=0):
	profile, _company = _context(pos_profile)
	frappe.has_permission("Item Group", "read", throw=True)
	filters = {} if int(include_parents or 0) else {"is_group": 0}
	groups = frappe.get_list("Item Group", filters=filters, fields=["name", "is_group", "lft", "rgt"], order_by="name", limit=500)
	allowed = _allowed_item_groups(profile)
	if allowed:
		groups = [row for row in groups if row.name in allowed or allowed.intersection(set(
			frappe.get_all(
				"Item Group",
				filters={"lft": ["between", [row.lft + 1, row.rgt - 1]]},
				pluck="name",
			)
		) | set(
			frappe.get_all("Item Group", filters={"lft": ["<", row.lft], "rgt": [">", row.rgt]}, pluck="name")
		))]
	return groups if int(include_parents or 0) else [row.name for row in groups]


@frappe.whitelist()
def get_item_prices(item_code, pos_profile=None):
	profile, company = _context(pos_profile)
	assert_doc_permission("Item", item_code)
	selling, buying = _catalog_price_lists(profile, company)
	prices = frappe.get_list(
		"Item Price",
		filters={"item_code": item_code, "price_list": ["in", [selling.name, buying.name]]},
		fields=["name", "price_list", "price_list_rate", "selling", "buying", "currency", "uom", "valid_from", "valid_upto"],
		order_by="price_list asc, uom asc, valid_from desc",
		limit=200,
	)
	return {"selling_price_list": selling.name, "buying_price_list": buying.name, "all_prices": prices}


@frappe.whitelist()
def update_item_prices(
	item_code,
	selling_price=None,
	buying_price=None,
	uom=None,
	valid_from=None,
	valid_upto=None,
	selling_price_list=None,
	buying_price_list=None,
	pos_profile=None,
):
	profile, company = _context(pos_profile)
	item = assert_doc_permission("Item", item_code)
	frappe.has_permission("Item Price", "write", throw=True)
	uom = uom or item.stock_uom
	_assert_uom(uom)
	if valid_from and valid_upto and getdate(valid_upto) < getdate(valid_from):
		frappe.throw(_("Valid Until cannot be before Valid From"))
	allowed_selling, allowed_buying = _catalog_price_lists(profile, company)
	if selling_price_list and selling_price_list != allowed_selling.name:
		frappe.throw(_("Selling Price List is outside this POS Profile"), frappe.PermissionError)
	if buying_price_list and buying_price_list != allowed_buying.name:
		frappe.throw(_("Buying Price List is outside this company"), frappe.PermissionError)
	updated = []
	if selling_price is not None:
		updated.append(_upsert_item_price(item_code, allowed_selling, flt(selling_price), uom, valid_from, valid_upto))
	if buying_price is not None:
		updated.append(_upsert_item_price(item_code, allowed_buying, flt(buying_price), uom, valid_from, valid_upto))
	return {"item_code": item_code, "prices": updated}


def _upsert_item_price(item_code, price_list, rate, uom, valid_from=None, valid_upto=None):
	if rate <= 0:
		frappe.throw(_("Item Price must be greater than zero"))
	filters = {
		"item_code": item_code,
		"price_list": price_list.name,
		"uom": uom,
		"supplier": ["is", "not set"],
		"customer": ["is", "not set"],
		"batch_no": ["is", "not set"],
		"valid_upto": getdate(valid_upto) if valid_upto else ["is", "not set"],
	}
	if valid_from:
		filters["valid_from"] = getdate(valid_from)
	existing = frappe.get_list(
		"Item Price", filters=filters, pluck="name", order_by="valid_from desc", limit=2
	)
	if len(existing) > 1:
		frappe.throw(_("Duplicate Item Prices already exist; resolve them in ERPNext before updating"))
	if existing:
		doc = assert_doc_permission("Item Price", existing[0], "write")
		doc.price_list_rate = rate
		doc.save(ignore_permissions=False)
	else:
		doc = frappe.get_doc({
			"doctype": "Item Price",
			"item_code": item_code,
			"price_list": price_list.name,
			"uom": uom,
			"price_list_rate": rate,
			"valid_from": getdate(valid_from) if valid_from else None,
			"valid_upto": getdate(valid_upto) if valid_upto else None,
		}).insert(ignore_permissions=False)
	return {"name": doc.name, "price_list": doc.price_list, "rate": flt(doc.price_list_rate), "uom": doc.uom}


# ── Classic item screen: list / query / create / update / delete ──────────────────────────────
# One master–detail screen: Add creates a new item and adds the purchased quantity to stock; Edit
# (admin-only via Item write) modifies a selected item's fields/qty/prices. Stock is written through
# the shared Stock Reconciliation mechanism (reused, not duplicated); prices are selling/buying
# Item Prices. سعر التجزئة is intentionally NOT part of this screen.


def _profile_warehouse(profile):
	return frappe.db.get_value("POS Profile", profile, "warehouse")


def _next_item_code():
	"""Auto item code — a clean, collision-free POS series (POS-ITM-00001, 00002, …). Item.autoname
	is `field:item_code` so the code is assigned explicitly. A plain max+1 sequence is avoided
	because this app also uses long barcode numbers as item codes, which would make a numeric
	sequence large and jumpy; the dedicated series stays clean and predictable."""
	from frappe.model.naming import make_autoname

	code = make_autoname("POS-ITM-.#####")
	while frappe.db.exists("Item", code):
		code = make_autoname("POS-ITM-.#####")
	return code


def _stock_map(item_codes, warehouse):
	"""{item_code: {qty, reserved, available}} for one warehouse — single query, no N+1."""
	if not item_codes or not warehouse:
		return {}
	out = {}
	for row in frappe.get_all(
		"Bin",
		filters={"item_code": ["in", list(item_codes)], "warehouse": warehouse},
		fields=["item_code", "actual_qty", "reserved_qty"],
	):
		actual, reserved = flt(row.actual_qty), flt(row.reserved_qty)
		out[row.item_code] = {"qty": actual, "reserved": reserved, "available": actual - reserved}
	return out


def _price_map(item_codes, selling_list, buying_list):
	"""{item_code: {cost, selling}} — single query."""
	if not item_codes:
		return {}
	out = {}
	for row in frappe.get_all(
		"Item Price",
		filters={"item_code": ["in", list(item_codes)], "price_list": ["in", [selling_list, buying_list]]},
		fields=["item_code", "price_list", "price_list_rate"],
		order_by="valid_from asc",
	):
		bucket = out.setdefault(row.item_code, {})
		if row.price_list == selling_list:
			bucket["selling"] = flt(row.price_list_rate)
		elif row.price_list == buying_list:
			bucket["cost"] = flt(row.price_list_rate)
	return out


def _barcode_map(item_codes):
	if not item_codes:
		return {}
	out = {}
	for row in frappe.get_all("Item Barcode", filters={"parent": ["in", list(item_codes)]}, fields=["parent", "barcode"]):
		out.setdefault(row.parent, row.barcode)
	return out


def _serialize_catalog_item(item, profile, company):
	warehouse = _profile_warehouse(profile)
	selling, buying = _catalog_price_lists(profile, company)
	stock = _stock_map([item.name], warehouse).get(item.name, {})
	prices = _price_map([item.name], selling.name, buying.name).get(item.name, {})
	return {
		"item_code": item.name,
		"item_name": item.item_name,
		"item_group": item.item_group,
		"stock_uom": item.stock_uom,
		"description": item.description,
		"image": item.image,
		"serial": item.get("custom_pos_serial"),
		"barcode": _barcode_map([item.name]).get(item.name),
		"qty": stock.get("qty", 0),
		"available": stock.get("available", 0),
		"cost_price": prices.get("cost", 0),
		"selling_price": prices.get("selling", 0),
		"disabled": cint(item.disabled),
	}


def _apply_stock_and_prices(profile, company, item_code, uom, *, qty, cost, selling, current_qty):
	"""Write stock via reconciliation when qty changes (which also syncs the prices); otherwise
	upsert the selling/buying Item Prices directly. Reuses the shared inventory reconciliation."""
	qty, cost, selling, current_qty = flt(qty), flt(cost), flt(selling), flt(current_qty)
	if qty < 0:
		frappe.throw(_("Quantity cannot be negative"))
	if qty > 0 and cost <= 0:
		frappe.throw(_("Enter a cost price for a positive stock quantity"))
	if qty != current_qty:
		from pos_next.api.inventory import submit_pos_stock_reconciliation

		submit_pos_stock_reconciliation(
			pos_profile=profile,
			purpose="Stock Reconciliation",
			rows=[{"item_code": item_code, "qty": qty, "buying_rate": cost, "selling_rate": selling}],
		)
	else:
		selling_list, buying_list = _catalog_price_lists(profile, company)
		if cost > 0:
			_upsert_item_price(item_code, buying_list, cost, uom)
		if selling > 0:
			_upsert_item_price(item_code, selling_list, selling, uom)


@frappe.whitelist()
def get_catalog_items(pos_profile=None, search=None, limit=200, offset=0):
	"""Rows for the classic grid — code, name, group, uom, qty, available, cost, selling, barcode,
	serial — ordered by code (creation order). Company-scoped, N+1-safe."""
	profile, company = _context(pos_profile)
	warehouse = _profile_warehouse(profile)
	selling, buying = _catalog_price_lists(profile, company)
	filters = {}
	if is_multi_company_site() and frappe.db.has_column("Item", OWNERSHIP_FIELD):
		filters[OWNERSHIP_FIELD] = company
	or_filters = None
	if search:
		like = f"%{search}%"
		or_filters = [["item_name", "like", like], ["item_code", "like", like], ["custom_pos_serial", "like", like]]
		barcode_items = frappe.get_all("Item Barcode", filters={"barcode": ["like", like]}, pluck="parent")
		if barcode_items:
			or_filters.append(["name", "in", barcode_items])
	items = frappe.get_list(
		"Item",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "item_name", "item_group", "stock_uom", "description", "image", "custom_pos_serial", "disabled"],
		order_by="creation asc",
		limit=min(cint(limit) or 200, 1000),
		start=cint(offset),
	)
	codes = [row.name for row in items]
	stock = _stock_map(codes, warehouse)
	prices = _price_map(codes, selling.name, buying.name)
	barcodes = _barcode_map(codes)
	rows = []
	for row in items:
		s = stock.get(row.name, {})
		p = prices.get(row.name, {})
		rows.append({
			"item_code": row.name,
			"item_name": row.item_name,
			"item_group": row.item_group,
			"stock_uom": row.stock_uom,
			"description": row.description,
			"image": row.image,
			"serial": row.get("custom_pos_serial"),
			"barcode": barcodes.get(row.name),
			"qty": s.get("qty", 0),
			"available": s.get("available", 0),
			"cost_price": p.get("cost", 0),
			"selling_price": p.get("selling", 0),
			"disabled": cint(row.disabled),
		})
	return {"items": rows, "warehouse": warehouse, "currency": selling.currency}


@frappe.whitelist()
def get_catalog_item(item_code, pos_profile=None):
	profile, company = _context(pos_profile)
	item = assert_doc_permission("Item", item_code)
	return _serialize_catalog_item(item, profile, company)


@frappe.whitelist()
def create_catalog_item(
	item_name,
	item_group,
	stock_uom="Nos",
	qty=0,
	cost_price=0,
	selling_price=0,
	barcode=None,
	serial=None,
	description=None,
	image=None,
	pos_profile=None,
):
	"""Add: create a new item with an auto code and add the purchased quantity to stock."""
	profile, company = _context(pos_profile)
	frappe.has_permission("Item", "create", throw=True)
	item_name = (item_name or "").strip()
	if not item_name:
		frappe.throw(_("Item Name is required"))
	_assert_item_group(item_group, profile)
	_assert_uom(stock_uom)
	_assert_barcode_unique(barcode)
	item_code = _next_item_code()

	frappe.db.savepoint("posnext_catalog_create")
	try:
		item_data = {
			"doctype": "Item",
			"item_code": item_code,
			"item_name": item_name,
			"company": company,
			"item_group": item_group,
			"stock_uom": stock_uom,
			"is_sales_item": 1,
			"is_purchase_item": 1,
			"is_stock_item": 1,
			"description": (description or "").strip() or None,
			"image": image or None,
			"custom_pos_serial": (serial or "").strip() or None,
			"barcodes": [{"barcode": barcode}] if barcode else [],
		}
		if is_multi_company_site() and frappe.db.has_column("Item", OWNERSHIP_FIELD):
			item_data[OWNERSHIP_FIELD] = company
		# Caller is already authorized above (catalog feature + Item `create` permission + company
		# scope); the company-isolation `validate` hook still binds the new item to the active
		# company. ignore_permissions only bypasses the doc-level strict user-permission check,
		# which for a NEW company-owned Item defers to a check a warehouse-scoped manager fails —
		# even though they legitimately manage their own company's catalog.
		doc = frappe.get_doc(item_data).insert(ignore_permissions=True)
		_apply_stock_and_prices(profile, company, doc.name, stock_uom, qty=qty, cost=cost_price, selling=selling_price, current_qty=0)
		return _serialize_catalog_item(frappe.get_doc("Item", doc.name), profile, company)
	except Exception:
		frappe.db.rollback(save_point="posnext_catalog_create")
		raise


@frappe.whitelist()
def update_catalog_item(
	item_code,
	item_name=None,
	item_group=None,
	stock_uom=None,
	qty=None,
	cost_price=None,
	selling_price=None,
	barcode=None,
	serial=None,
	description=None,
	image=None,
	pos_profile=None,
):
	"""Edit (admin-only via Item write): update a selected item's fields, stock and prices."""
	profile, company = _context(pos_profile)
	item = assert_doc_permission("Item", item_code, "write")

	if item_name is not None and item_name.strip():
		item.item_name = item_name.strip()
	if item_group is not None:
		_assert_item_group(item_group, profile)
		item.item_group = item_group
	if stock_uom is not None:
		_assert_uom(stock_uom)
		item.stock_uom = stock_uom
	if description is not None:
		item.description = description.strip() or None
	if image is not None:
		item.image = image or None
	if serial is not None:
		item.custom_pos_serial = serial.strip() or None
	if barcode is not None:
		_assert_barcode_unique(barcode, item_code)
		item.set("barcodes", [{"barcode": barcode}] if barcode else [])
	item.save(ignore_permissions=False)

	if qty is not None or cost_price is not None or selling_price is not None:
		warehouse = _profile_warehouse(profile)
		current_qty = _stock_map([item.name], warehouse).get(item.name, {}).get("qty", 0)
		selling_list, buying_list = _catalog_price_lists(profile, company)
		existing = _price_map([item.name], selling_list.name, buying_list.name).get(item.name, {})
		target_qty = flt(qty) if qty is not None else flt(current_qty)
		cost = flt(cost_price) if cost_price is not None else flt(existing.get("cost", 0))
		sell = flt(selling_price) if selling_price is not None else flt(existing.get("selling", 0))
		_apply_stock_and_prices(profile, company, item.name, item.stock_uom, qty=target_qty, cost=cost, selling=sell, current_qty=current_qty)

	return _serialize_catalog_item(frappe.get_doc("Item", item.name), profile, company)


@frappe.whitelist()
def delete_catalog_item(item_code, pos_profile=None):
	"""Delete (admin-only, requires Item write): hard-delete only when the caller actually holds
	Item delete permission and the item has no stock history; otherwise disable it (soft delete) —
	which is reversible, safe for items with history, and available to managers who lack delete."""
	profile, _company = _context(pos_profile)
	item = assert_doc_permission("Item", item_code, "write")
	has_history = bool(frappe.db.exists("Stock Ledger Entry", {"item_code": item.name}))
	if not has_history and frappe.has_permission("Item", "delete", doc=item):
		try:
			frappe.delete_doc("Item", item.name, ignore_permissions=False)
			return {"item_code": item.name, "deleted": True}
		except frappe.LinkExistsError:
			item.reload()
	if item.disabled:
		return {"item_code": item.name, "deleted": False, "disabled": True}
	item.disabled = 1
	item.save(ignore_permissions=False)
	return {"item_code": item.name, "deleted": False, "disabled": True}
