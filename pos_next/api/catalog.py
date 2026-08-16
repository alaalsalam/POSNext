"""Flag-controlled, profile-scoped catalog management APIs."""

import frappe
from frappe import _
from frappe.utils import flt, getdate

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
