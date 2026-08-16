"""Profile-scoped Purchase Invoice and supplier Payment Entry APIs."""

import json
from decimal import Decimal, InvalidOperation
from hashlib import sha256

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, nowdate

from pos_next.api.management_scope import (
	assert_company_resource,
	assert_doc_permission,
	lock_document,
	normalize_idempotency_key,
	require_feature_permission,
)
from pos_next.api.company_scope import OWNERSHIP_FIELD, is_multi_company_site

AMOUNT_TOLERANCE = 0.005
PURCHASE_FIELDS = {
	"supplier", "posting_date", "due_date", "bill_no", "bill_date", "update_stock",
	"currency", "conversion_rate", "plc_conversion_rate", "buying_price_list", "apply_discount_on",
	"discount_amount", "additional_discount_percentage", "remarks", "taxes_and_charges",
	"credit_to", "set_warehouse",
}
ITEM_FIELDS = {
	"item_code", "item_name", "description", "qty", "uom", "conversion_factor", "rate",
	"warehouse", "expense_account", "cost_center",
}
TAX_FIELDS = {
	"charge_type", "account_head", "description", "rate", "tax_amount",
	"included_in_print_rate", "cost_center", "add_deduct_tax", "category", "row_id",
	"reference_row",
}
PURCHASE_NUMERIC_FIELDS = {
	"additional_discount_percentage", "conversion_rate", "discount_amount",
	"plc_conversion_rate", "update_stock",
}
ITEM_NUMERIC_FIELDS = {"conversion_factor", "qty", "rate"}
TAX_NUMERIC_FIELDS = {"included_in_print_rate", "rate", "tax_amount"}
DATE_FIELDS = {"bill_date", "due_date", "posting_date", "reference_date"}


def _context(feature, pos_profile=None, company=None):
	return require_feature_permission(
		feature, "Purchase Invoice", "read", pos_profile=pos_profile, company=company
	)


def _parse_data(data):
	if isinstance(data, str):
		try:
			data = json.loads(data)
		except (TypeError, ValueError):
			frappe.throw(_("Invalid purchase invoice data"))
	if not isinstance(data, dict):
		frappe.throw(_("Purchase invoice data must be an object"))
	return data


def _purchase_doc_result(doc):
	return {
		"name": doc.name,
		"modified": str(doc.modified),
		"docstatus": doc.docstatus,
		"status": doc.status,
		"company": doc.company,
		"currency": doc.currency,
		"total": flt(doc.total),
		"total_taxes_and_charges": flt(doc.total_taxes_and_charges),
		"grand_total": flt(doc.grand_total),
		"outstanding_amount": flt(doc.outstanding_amount),
	}


def _canonical_number(value, default=0):
	try:
		number = Decimal(str(default if value in (None, "") else value))
	except InvalidOperation:
		frappe.throw(_("Invalid numeric value in idempotent request"))
	if number == 0:
		return "0"
	return format(number.normalize(), "f")


def _canonical_value(field, value, *, numeric_fields=()):
	if field in numeric_fields:
		default = 1 if field in {"conversion_factor", "conversion_rate", "plc_conversion_rate"} else 0
		return _canonical_number(value, default)
	if field in DATE_FIELDS:
		return str(getdate(value)) if value else None
	if value is None:
		return None
	return str(value).strip()


def _request_fingerprint(request):
	serialized = json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
	return sha256(serialized.encode("utf-8")).hexdigest()


def _purchase_request_fingerprint(payload):
	"""Bind an idempotency key to every accepted, financially material input."""
	header = {
		field: _canonical_value(field, payload.get(field), numeric_fields=PURCHASE_NUMERIC_FIELDS)
		for field in sorted(PURCHASE_FIELDS | {"company", "custom_posnext_pos_profile"})
	}
	items = []
	for row in payload.get("items") or []:
		canonical = {
			field: _canonical_value(field, row.get(field), numeric_fields=ITEM_NUMERIC_FIELDS)
			for field in sorted(ITEM_FIELDS)
		}
		if cint(payload.get("update_stock")):
			canonical["warehouse"] = str(row.get("warehouse") or payload.get("set_warehouse") or "").strip()
		items.append(canonical)
	taxes = [
		{
			field: _canonical_value(field, row.get(field), numeric_fields=TAX_NUMERIC_FIELDS)
			for field in sorted(TAX_FIELDS)
		}
		for row in payload.get("taxes") or []
	]
	return _request_fingerprint({"header": header, "items": items, "taxes": taxes})


def _payment_request_fingerprint(request):
	return _request_fingerprint({
		"invoice_name": str(request["invoice_name"]).strip(),
		"amount": _canonical_number(request["amount"]),
		"paid_from": str(request["paid_from"]).strip(),
		"posting_date": _canonical_value("posting_date", request["posting_date"]),
		"reference_date": _canonical_value("reference_date", request["reference_date"]),
		"mode_of_payment": _canonical_value("mode_of_payment", request.get("mode_of_payment")),
		"reference_no": _canonical_value("reference_no", request.get("reference_no")),
		"remarks": _canonical_value("remarks", request.get("remarks")),
		"company": str(request["company"]).strip(),
		"pos_profile": str(request["pos_profile"]).strip(),
	})


def _assert_request_fingerprint(doc, expected, label):
	stored = doc.get("custom_posnext_request_fingerprint")
	if not stored or stored != expected:
		frappe.throw(
			_("This idempotency key conflicts with a different {0} request").format(_(label)),
			frappe.ValidationError,
		)


def _assert_profile_document(doc, profile, company):
	if doc.company != company:
		frappe.throw(_("The document belongs to a different company"), frappe.PermissionError)
	if doc.get("custom_posnext_pos_profile") != profile:
		frappe.throw(_("The document belongs to a different POS Profile"), frappe.PermissionError)


def _assert_supplier(name):
	doc = assert_doc_permission("Supplier", name)
	if doc.disabled:
		frappe.throw(_("The selected Supplier is disabled"))
	return doc


def _assert_price_list(name, company):
	doc = assert_doc_permission("Price List", name)
	if not doc.enabled or not doc.buying:
		frappe.throw(_("The selected Price List is not enabled for buying"))
	return doc


def _default_buying_price_list(company):
	"""Resolve a usable buying price list.

	Falls back to the first enabled buying price list when Buying Settings is unset or
	(as seen in the wild) points at a selling list, so purchase mode doesn't hard-fail on
	a misconfigured default.
	"""
	configured = frappe.db.get_single_value("Buying Settings", "buying_price_list")
	if configured and frappe.db.get_value("Price List", configured, ["enabled", "buying"]) == (1, 1):
		return configured
	fallback = frappe.db.get_value("Price List", {"enabled": 1, "buying": 1}, "name", order_by="creation")
	return fallback or configured or "Standard Buying"


def _validate_currency(currency, company, conversion_rate):
	assert_doc_permission("Currency", currency)
	company_currency = frappe.db.get_value("Company", company, "default_currency")
	if currency != company_currency and flt(conversion_rate) <= 0:
		frappe.throw(_("A positive conversion rate is required for a foreign-currency invoice"))


def _validate_purchase_payload(data, profile, company):
	unknown = set(data) - PURCHASE_FIELDS - {
		"name", "modified", "expected_modified", "idempotency_key", "company", "items", "taxes"
	}
	if unknown:
		frappe.throw(_("Unsupported purchase invoice fields: {0}").format(", ".join(sorted(unknown))))
	if not data.get("supplier"):
		frappe.throw(_("Supplier is required"))
	_assert_supplier(data["supplier"])
	price_list = data.get("buying_price_list") or _default_buying_price_list(company)
	price_list_doc = _assert_price_list(price_list, company)
	currency = data.get("currency") or frappe.db.get_value("Company", company, "default_currency")
	_validate_currency(currency, company, data.get("conversion_rate"))
	if price_list_doc.currency != currency and flt(data.get("plc_conversion_rate")) <= 0:
		frappe.throw(_("A positive Price List Currency conversion rate is required"))
	items = data.get("items")
	if not isinstance(items, list) or not items:
		frappe.throw(_("At least one purchase item is required"))
	clean_items = []
	for index, row in enumerate(items, 1):
		if not isinstance(row, dict) or set(row) - ITEM_FIELDS:
			frappe.throw(_("Unsupported fields in purchase item row {0}").format(index))
		item = assert_doc_permission("Item", row.get("item_code"))
		if item.disabled or not item.is_purchase_item:
			frappe.throw(_("Item {0} is not enabled for purchasing").format(item.name))
		if flt(row.get("qty")) <= 0 or flt(row.get("rate")) < 0:
			frappe.throw(_("Quantity must be positive and rate cannot be negative in row {0}").format(index))
		# Receiving stock at a zero rate would book 0-cost inventory (ERPNext rejects it late with a
		# cryptic "Allow Zero Valuation Rate" error); require an actual buying price, named clearly.
		if cint(data.get("update_stock")) and flt(row.get("rate")) <= 0:
			frappe.throw(_("Enter a purchase price for item {0}").format(item.item_name or item.name))
		uom = row.get("uom") or item.stock_uom
		assert_doc_permission("UOM", uom)
		warehouse = row.get("warehouse") or data.get("set_warehouse")
		if cint(data.get("update_stock")) and not warehouse:
			frappe.throw(_("Warehouse is required when Update Stock is enabled"))
		if warehouse:
			assert_company_resource("Warehouse", warehouse, company)
		if row.get("expense_account"):
			assert_company_resource("Account", row["expense_account"], company)
		if row.get("cost_center"):
			assert_company_resource("Cost Center", row["cost_center"], company)
		clean_items.append({field: row.get(field) for field in ITEM_FIELDS if row.get(field) is not None} | {"uom": uom})
	clean_taxes = []
	for index, row in enumerate(data.get("taxes") or [], 1):
		if not isinstance(row, dict) or set(row) - TAX_FIELDS:
			frappe.throw(_("Unsupported fields in tax row {0}").format(index))
		if row.get("account_head"):
			assert_company_resource("Account", row["account_head"], company)
		if row.get("cost_center"):
			assert_company_resource("Cost Center", row["cost_center"], company)
		clean_taxes.append({field: row.get(field) for field in TAX_FIELDS if row.get(field) is not None})
	if data.get("credit_to"):
		account = assert_company_resource("Account", data["credit_to"], company)
		if account.root_type != "Liability":
			frappe.throw(_("Credit To must be a liability account"))
	if data.get("taxes_and_charges"):
		assert_company_resource(
			"Purchase Taxes and Charges Template",
			data["taxes_and_charges"],
			company,
		)
	payload = {
		**{field: data.get(field) for field in PURCHASE_FIELDS if data.get(field) is not None},
		"company": company,
		"buying_price_list": price_list,
		"currency": currency,
		"items": clean_items,
		"taxes": clean_taxes,
		"custom_posnext_pos_profile": profile,
	}
	payload["posting_date"] = getdate(data.get("posting_date") or nowdate())
	for field in ("due_date", "bill_date"):
		if payload.get(field):
			payload[field] = getdate(payload[field])
	payload["update_stock"] = cint(payload.get("update_stock"))
	payload["conversion_rate"] = flt(payload.get("conversion_rate") or 1)
	payload["plc_conversion_rate"] = flt(payload.get("plc_conversion_rate") or 1)
	return payload


def _get_purchase_invoice(name, profile, company, ptype="read"):
	doc = assert_doc_permission("Purchase Invoice", name, ptype)
	_assert_profile_document(doc, profile, company)
	return doc


def _get_payable_invoice(name, profile=None, company=None, *, lock=False):
	if lock:
		lock_document("Purchase Invoice", name, ["name", "outstanding_amount"])
	doc = assert_doc_permission("Purchase Invoice", name)
	if profile and company:
		_assert_profile_document(doc, profile, company)
	if doc.docstatus != 1:
		frappe.throw(_("Only submitted purchase invoices can be paid"))
	if flt(doc.outstanding_amount) <= AMOUNT_TOLERANCE:
		frappe.throw(_("This purchase invoice has no outstanding amount"))
	return doc


def _validate_payment_amount(amount, outstanding):
	amount = flt(amount)
	if amount <= 0:
		frappe.throw(_("Payment amount must be greater than zero"))
	if amount > flt(outstanding) + AMOUNT_TOLERANCE:
		frappe.throw(_("Payment amount exceeds the current outstanding amount"))
	return amount


@frappe.whitelist()
def get_suppliers(search="", limit=30, pos_profile=None):
	_profile, company = _context("purchases", pos_profile)
	frappe.has_permission("Supplier", "read", throw=True)
	filters = {"disabled": 0}
	if is_multi_company_site() and frappe.db.has_column("Supplier", OWNERSHIP_FIELD):
		filters[OWNERSHIP_FIELD] = company
	if search:
		filters["supplier_name"] = ["like", f"%{search}%"]
	return frappe.get_list("Supplier", filters=filters, fields=["name", "supplier_name", "supplier_group", "supplier_type"], order_by="supplier_name", limit=min(cint(limit), 100))


@frappe.whitelist()
def get_supplier_groups(pos_profile=None):
	_profile, company = _context("purchases", pos_profile)
	frappe.has_permission("Supplier Group", "read", throw=True)
	filters = {"is_group": 0}
	if is_multi_company_site() and frappe.db.has_column("Supplier Group", OWNERSHIP_FIELD):
		filters[OWNERSHIP_FIELD] = company
	return frappe.get_list("Supplier Group", filters=filters, fields=["name"], order_by="name", limit=200)


@frappe.whitelist()
def create_supplier(supplier_name, supplier_group, supplier_type="Company", pos_profile=None, mobile_no=None):
	_profile, company = _context("purchases", pos_profile)
	frappe.has_permission("Supplier", "create", throw=True)
	supplier_name = (supplier_name or "").strip()
	if not supplier_name:
		frappe.throw(_("Supplier name is required"))
	from pos_next.api.party_contacts import require_mobile_no

	require_mobile_no(mobile_no, "Supplier")
	group = assert_doc_permission("Supplier Group", supplier_group)
	if group.is_group:
		frappe.throw(_("Supplier Group must be a leaf group"))
	if supplier_type not in {"Company", "Individual"}:
		frappe.throw(_("Invalid Supplier Type"))
	existing = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
	if existing:
		doc = assert_doc_permission("Supplier", existing)
		return {"name": doc.name, "supplier_name": doc.supplier_name, "created": False}
	data = {
		"doctype": "Supplier",
		"supplier_name": supplier_name,
		"supplier_group": supplier_group,
		"supplier_type": supplier_type,
		"mobile_no": mobile_no.strip(),
		"custom_pos_mobile_no": mobile_no.strip(),
	}
	if is_multi_company_site() and frappe.db.has_column("Supplier", OWNERSHIP_FIELD):
		data[OWNERSHIP_FIELD] = company
	doc = frappe.get_doc(data).insert(ignore_permissions=False)
	return {"name": doc.name, "supplier_name": doc.supplier_name, "created": True}


@frappe.whitelist()
def get_purchase_invoices(supplier=None, status=None, from_date=None, to_date=None, search=None, limit=50, start=0, pos_profile=None):
	profile, company = _context("purchases", pos_profile)
	frappe.has_permission("Purchase Invoice", "read", throw=True)
	filters = {"company": company, "custom_posnext_pos_profile": profile}
	for key, value in (("supplier", supplier), ("status", status)):
		if value:
			filters[key] = value
	if from_date and to_date:
		filters["posting_date"] = ["between", [getdate(from_date), getdate(to_date)]]
	elif from_date:
		filters["posting_date"] = [">=", getdate(from_date)]
	elif to_date:
		filters["posting_date"] = ["<=", getdate(to_date)]
	if search:
		filters["name"] = ["like", f"%{search}%"]
	fields = ["name", "supplier", "supplier_name", "posting_date", "due_date", "grand_total", "total_taxes_and_charges", "outstanding_amount", "status", "docstatus", "bill_no", "currency", "modified"]
	rows = frappe.get_list("Purchase Invoice", filters=filters, fields=fields, order_by="posting_date desc, creation desc", limit=min(cint(limit), 100), start=cint(start))
	total = len(frappe.get_list("Purchase Invoice", filters=filters, pluck="name", limit=0))
	return {"invoices": rows, "total": total}


@frappe.whitelist()
def get_purchase_invoice(name, pos_profile=None):
	profile, company = _context("purchases", pos_profile)
	return _get_purchase_invoice(name, profile, company).as_dict()


@frappe.whitelist()
def get_new_purchase_invoice_defaults(pos_profile=None):
	profile, company = _context("purchases", pos_profile)
	frappe.has_permission("Purchase Invoice", "create", throw=True)
	price_list = _default_buying_price_list(company)
	price = _assert_price_list(price_list, company)
	settings = frappe.db.get_value(
		"POS Settings",
		{"pos_profile": profile},
		[
			"posa_default_supplier",
			"posa_default_purchase_warehouse",
			"posa_default_purchase_tax_template",
			"posa_default_expense_account",
		],
		as_dict=True,
	) or {}
	default_currency = frappe.db.get_value("Company", company, "default_currency")
	return {
		"pos_profile": profile,
		"company": company,
		"posting_date": nowdate(),
		"due_date": add_days(nowdate(), 30),
		"buying_price_list": price.name,
		"price_list_currency": price.currency,
		"currency": default_currency,
		"company_currency": default_currency,
		# Configurable purchase defaults (mirror the sales default customer) so
		# Purchase mode opens pre-filled. Cashier can still change any of them.
		"default_supplier": settings.get("posa_default_supplier"),
		"default_supplier_name": frappe.db.get_value(
			"Supplier", settings.get("posa_default_supplier"), "supplier_name"
		)
		if settings.get("posa_default_supplier")
		else None,
		# The receiving warehouse has no on-screen picker in purchase mode, so it must
		# resolve to something valid: the configured default, else the profile's own
		# warehouse (the restricted cashier's permitted leaf), so day-one purchases work
		# before anyone visits Settings. Tax template / expense account stay opt-in
		# (settings-value-or-omit) — no silent VAT or expense injection.
		"default_warehouse": settings.get("posa_default_purchase_warehouse")
		or frappe.db.get_value("POS Profile", profile, "warehouse"),
		"default_tax_template": settings.get("posa_default_purchase_tax_template"),
		"default_expense_account": settings.get("posa_default_expense_account"),
	}


@frappe.whitelist()
def get_purchase_currencies(pos_profile=None):
	_context("purchases", pos_profile)
	frappe.has_permission("Currency", "read", throw=True)
	return frappe.get_list("Currency", filters={"enabled": 1}, fields=["name", "fraction", "fraction_units"], order_by="name", limit=200)


@frappe.whitelist()
def save_purchase_invoice(data, idempotency_key=None, expected_modified=None, pos_profile=None):
	data = _parse_data(data)
	profile, company = _context("purchases", pos_profile, data.get("company"))
	name = data.get("name")
	if name:
		frappe.has_permission("Purchase Invoice", "write", throw=True)
		locked = lock_document("Purchase Invoice", name, ["name", "modified", "docstatus"])
		doc = _get_purchase_invoice(name, profile, company, "write")
		if doc.docstatus != 0:
			frappe.throw(_("Only draft purchase invoices can be edited"))
		expected = str(expected_modified or data.get("expected_modified") or "")
		if not expected or expected != str(locked.modified):
			frappe.throw(_("This draft changed after you opened it. Reload before saving."), frappe.TimestampMismatchError)
		payload = _validate_purchase_payload(data, profile, company)
		payload["custom_posnext_request_fingerprint"] = _purchase_request_fingerprint(payload)
		for field, value in payload.items():
			doc.set(field, value)
		doc.save(ignore_permissions=False)
		return _purchase_doc_result(doc)

	frappe.has_permission("Purchase Invoice", "create", throw=True)
	key = normalize_idempotency_key(idempotency_key or data.get("idempotency_key"))
	payload = _validate_purchase_payload(data, profile, company)
	fingerprint = _purchase_request_fingerprint(payload)
	existing = frappe.db.get_value("Purchase Invoice", {"custom_posnext_idempotency_key": key}, "name")
	if existing:
		doc = _get_purchase_invoice(existing, profile, company)
		_assert_request_fingerprint(doc, fingerprint, "Purchase Invoice")
		return {**_purchase_doc_result(doc), "idempotent_replay": True}
	payload["custom_posnext_idempotency_key"] = key
	payload["custom_posnext_request_fingerprint"] = fingerprint
	frappe.db.savepoint("posnext_purchase_create")
	try:
		doc = frappe.get_doc({"doctype": "Purchase Invoice", **payload}).insert(ignore_permissions=False)
		return {**_purchase_doc_result(doc), "idempotent_replay": False}
	except frappe.UniqueValidationError:
		frappe.db.rollback(save_point="posnext_purchase_create")
		existing = frappe.db.get_value("Purchase Invoice", {"custom_posnext_idempotency_key": key}, "name")
		if existing:
			doc = _get_purchase_invoice(existing, profile, company)
			_assert_request_fingerprint(doc, fingerprint, "Purchase Invoice")
			return {**_purchase_doc_result(doc), "idempotent_replay": True}
		raise
	except Exception:
		frappe.db.rollback(save_point="posnext_purchase_create")
		raise


@frappe.whitelist()
def submit_purchase_invoice(name, expected_modified, pos_profile=None):
	profile, company = _context("purchases", pos_profile)
	frappe.has_permission("Purchase Invoice", "submit", throw=True)
	locked = lock_document("Purchase Invoice", name, ["name", "modified", "docstatus"])
	doc = _get_purchase_invoice(name, profile, company, "submit")
	if doc.docstatus != 0:
		frappe.throw(_("Invoice is not in Draft status"))
	if str(locked.modified) != str(expected_modified or ""):
		frappe.throw(_("This draft changed after you opened it. Reload before submitting."), frappe.TimestampMismatchError)
	doc.submit()
	return _purchase_doc_result(doc)


@frappe.whitelist()
def cancel_purchase_invoice(name, pos_profile=None):
	profile, company = _context("purchases", pos_profile)
	frappe.has_permission("Purchase Invoice", "cancel", throw=True)
	lock_document("Purchase Invoice", name)
	doc = _get_purchase_invoice(name, profile, company, "cancel")
	if doc.docstatus != 1:
		frappe.throw(_("Invoice is not submitted"))
	doc.cancel()
	return _purchase_doc_result(doc)


@frappe.whitelist()
def get_purchase_items(search="", limit=30, pos_profile=None):
	_context("purchases", pos_profile)
	frappe.has_permission("Item", "read", throw=True)
	filters = {"disabled": 0, "is_purchase_item": 1}
	if search:
		filters["item_name"] = ["like", f"%{search}%"]
	return frappe.get_list("Item", filters=filters, fields=["name as item_code", "item_name", "stock_uom", "item_group", "is_stock_item"], order_by="item_name", limit=min(cint(limit), 100))


# Which source to pre-fill the purchase price from (configured per profile in POS Settings). Each
# option is the PRIMARY source; the remaining sources are tried in order as fallbacks so the cashier
# rarely sees 0. Keys: price_list (buying price list), last_purchase (Item.last_purchase_rate,
# maintained by ERPNext on every purchase submit), valuation (Item.valuation_rate / average cost).
_PURCHASE_PRICE_SOURCE_ORDERS = {
	"Buying Price List": ("price_list", "last_purchase", "valuation"),
	"Last Purchase Rate": ("last_purchase", "price_list", "valuation"),
	"Valuation Rate": ("valuation", "last_purchase", "price_list"),
}


def _purchase_price_source_order(profile):
	source = frappe.db.get_value("POS Settings", {"pos_profile": profile}, "posa_purchase_price_source")
	return _PURCHASE_PRICE_SOURCE_ORDERS.get(source, _PURCHASE_PRICE_SOURCE_ORDERS["Buying Price List"])


def _pick_by_source(order, by_source):
	"""First source in `order` with a positive rate wins; 0 when none has one."""
	for src in order:
		if flt(by_source.get(src)) > 0:
			return flt(by_source[src])
	return 0.0


@frappe.whitelist()
def get_item_buying_price(item_code, buying_price_list=None, uom=None, pos_profile=None):
	profile, company = _context("purchases", pos_profile)
	item = assert_doc_permission("Item", item_code)
	price_list = _assert_price_list(buying_price_list or _default_buying_price_list(company), company)
	filters = {"item_code": item.name, "price_list": price_list.name, "buying": 1, "uom": uom or item.stock_uom}
	prices = frappe.get_list("Item Price", filters=filters, fields=["name", "price_list_rate", "currency", "uom", "valid_from", "valid_upto"], order_by="valid_from desc", limit=2)
	if len(prices) > 1:
		frappe.throw(_("Multiple applicable buying prices exist; select the rate explicitly"))
	# Pre-fill the rate from the profile's configured source (with fallback) instead of 0.
	buying_price = _pick_by_source(
		_purchase_price_source_order(profile),
		{
			"price_list": flt(prices[0].price_list_rate) if prices else 0.0,
			"last_purchase": flt(item.last_purchase_rate),
			"valuation": flt(item.valuation_rate),
		},
	)
	return {"item_code": item.name, "buying_price": buying_price, "price_list": price_list.name, "currency": price_list.currency}


@frappe.whitelist()
def get_buying_prices(buying_price_list=None, pos_profile=None):
	"""Bulk buying-price map so the POS grid can show purchase prices in one call (no per-item N+1).

	Each item's rate is taken from the profile's configured price source (POS Settings →
	posa_purchase_price_source) — Buying Price List / Last Purchase Rate / Valuation Rate — falling
	back through the other sources so purchase mode pre-fills a real cost instead of 0."""
	profile, company = _context("purchases", pos_profile)
	frappe.has_permission("Item Price", "read", throw=True)
	frappe.has_permission("Item", "read", throw=True)
	price_list = _assert_price_list(buying_price_list or _default_buying_price_list(company), company)
	order = _purchase_price_source_order(profile)

	pl_rates = {}
	for row in frappe.get_list(
		"Item Price",
		filters={"price_list": price_list.name, "buying": 1},
		fields=["item_code", "price_list_rate"],
		order_by="valid_from desc",
		limit=0,
	):
		# First occurrence wins (newest valid_from first); ignore later/duplicate rows.
		pl_rates.setdefault(row.item_code, flt(row.price_list_rate))
	item_rates = {
		item.name: (flt(item.last_purchase_rate), flt(item.valuation_rate))
		for item in frappe.get_list(
			"Item",
			filters={"disabled": 0, "is_purchase_item": 1},
			fields=["name", "last_purchase_rate", "valuation_rate"],
			limit=0,
		)
	}
	prices = {}
	for code in set(pl_rates) | set(item_rates):
		last_purchase, valuation = item_rates.get(code, (0.0, 0.0))
		rate = _pick_by_source(order, {"price_list": pl_rates.get(code, 0.0), "last_purchase": last_purchase, "valuation": valuation})
		if rate > 0:
			prices[code] = rate
	return {"price_list": price_list.name, "currency": price_list.currency, "prices": prices, "price_source": order[0]}


@frappe.whitelist()
def get_warehouses(pos_profile=None):
	_profile, company = _context("purchases", pos_profile)
	frappe.has_permission("Warehouse", "read", throw=True)
	return frappe.get_list("Warehouse", filters={"company": company, "is_group": 0, "disabled": 0}, fields=["name", "warehouse_name", "company"], order_by="warehouse_name", limit=200)


@frappe.whitelist()
def get_expense_accounts(pos_profile=None):
	_profile, company = _context("purchases", pos_profile)
	frappe.has_permission("Account", "read", throw=True)
	return frappe.get_list("Account", filters={"company": company, "is_group": 0, "disabled": 0, "root_type": ["in", ["Expense", "Asset"]]}, fields=["name", "account_name", "account_type"], order_by="account_name", limit=200)


@frappe.whitelist()
def get_purchase_tax_templates(pos_profile=None):
	_profile, company = _context("purchases", pos_profile)
	frappe.has_permission("Purchase Taxes and Charges Template", "read", throw=True)
	return frappe.get_list(
		"Purchase Taxes and Charges Template",
		filters={"company": company, "disabled": 0},
		fields=["name", "title", "is_default", "company"],
		order_by="is_default desc, title asc",
		limit=200,
	)


def _profile_payment_method_accounts(profile, company):
	"""The POS profile's configured payment methods, each mapped to its Cash/Bank account for
	this company (linked from settings). Used to drive the supplier-payment method tiles and to
	resolve/validate the payment account server-side so the client never handles account names."""
	methods = frappe.get_all(
		"POS Payment Method",
		filters={"parent": profile, "parenttype": "POS Profile"},
		fields=["mode_of_payment", "default", "idx"],
		order_by="idx",
	)
	mode_names = [row.mode_of_payment for row in methods]
	accounts = {
		row.parent: row.default_account
		for row in frappe.get_all(
			"Mode of Payment Account",
			filters={"company": company, "parent": ["in", mode_names or [""]]},
			fields=["parent", "default_account"],
			limit=0,
		)
	}
	return methods, accounts


def _resolve_payment_account(profile, company, mode_of_payment, paid_from):
	"""Resolve the Cash/Bank account for a supplier payment. `mode_of_payment` is the primary
	input — it must be one of the profile's configured methods, and its settings-mapped account
	is used. An explicit `paid_from` is accepted for back-compat but must match the mode's account."""
	resolved = paid_from or None
	if mode_of_payment:
		methods, accounts = _profile_payment_method_accounts(profile, company)
		if mode_of_payment not in {row.mode_of_payment for row in methods}:
			frappe.throw(_("This payment method is not enabled for this POS Profile"), frappe.PermissionError)
		mode_account = accounts.get(mode_of_payment)
		if not mode_account:
			frappe.throw(_("The payment method {0} has no account configured in Settings for this company").format(mode_of_payment))
		if resolved and resolved != mode_account:
			frappe.throw(_("The selected account does not match the payment method configured in Settings"))
		resolved = mode_account
	if not resolved:
		frappe.throw(_("A payment method is required"))
	account = assert_company_resource("Account", resolved, company)
	if account.account_type not in {"Cash", "Bank"}:
		frappe.throw(_("The payment account must be a Cash or Bank account"))
	return account.name


@frappe.whitelist()
def get_supplier_payment_defaults(invoice_name, pos_profile=None):
	profile, company = _context("supplier_payments", pos_profile)
	frappe.has_permission("Payment Entry", "create", throw=True)
	invoice = _get_payable_invoice(invoice_name, profile, company)
	methods, method_accounts = _profile_payment_method_accounts(profile, company)
	payment_methods = [
		{
			"mode_of_payment": row.mode_of_payment,
			"default": cint(row.default),
			# Server resolves the account; the UI only needs to know the method is usable.
			"account_missing": not bool(method_accounts.get(row.mode_of_payment)),
		}
		for row in methods
	]
	# Legacy keys kept additively so an older cached dialog bundle keeps working during rollout;
	# the new dialog uses `payment_methods` and never handles account names. Remove next pass.
	accounts = frappe.get_list("Account", filters={"company": company, "is_group": 0, "disabled": 0, "account_type": ["in", ["Cash", "Bank"]]}, fields=["name", "account_name", "account_type", "account_currency"], order_by="account_type, account_name", limit=200)
	modes = [{"name": row.mode_of_payment, "default_account": method_accounts.get(row.mode_of_payment)} for row in methods]
	return {
		"invoice": {"name": invoice.name, "supplier": invoice.supplier, "supplier_name": invoice.supplier_name, "company": company, "currency": invoice.currency, "grand_total": flt(invoice.grand_total), "outstanding_amount": flt(invoice.outstanding_amount)},
		"posting_date": nowdate(),
		"payment_methods": payment_methods,
		"accounts": accounts,
		"modes_of_payment": modes,
		"can_submit": bool(frappe.has_permission("Payment Entry", "submit")),
	}


def _payment_result(payment, invoice=None):
	if invoice:
		invoice.reload()
	return {
		"name": payment.name,
		"modified": str(payment.modified),
		"docstatus": payment.docstatus,
		"invoice": invoice.name if invoice else None,
		"outstanding_amount": flt(invoice.outstanding_amount) if invoice else None,
	}


@frappe.whitelist()
def create_supplier_payment(invoice_name, amount, paid_from=None, idempotency_key=None, posting_date=None, mode_of_payment=None, reference_no=None, reference_date=None, remarks=None, submit=0, pos_profile=None):
	profile, company = _context("supplier_payments", pos_profile)
	frappe.has_permission("Payment Entry", "create", throw=True)
	if cint(submit):
		frappe.has_permission("Payment Entry", "submit", throw=True)
	key = normalize_idempotency_key(idempotency_key)
	# The client sends the payment METHOD (from the profile's configured methods); the account is
	# resolved + validated here from Settings so account names never leave the server.
	resolved_from = _resolve_payment_account(profile, company, mode_of_payment, paid_from)
	posting_date = getdate(posting_date or nowdate())
	reference_date = getdate(reference_date or posting_date)
	fingerprint = _payment_request_fingerprint({
		"invoice_name": invoice_name,
		"amount": amount,
		"paid_from": paid_from,
		"posting_date": posting_date,
		"reference_date": reference_date,
		"mode_of_payment": mode_of_payment,
		"reference_no": reference_no,
		"remarks": remarks,
		"company": company,
		"pos_profile": profile,
	})
	existing = frappe.db.get_value("Payment Entry", {"custom_posnext_idempotency_key": key}, "name")
	if existing:
		payment = assert_doc_permission("Payment Entry", existing)
		_assert_profile_document(payment, profile, company)
		_assert_request_fingerprint(payment, fingerprint, "supplier payment")
		if payment.docstatus == 2:
			frappe.throw(_("A cancelled payment cannot be replayed"))
		invoice = assert_doc_permission("Purchase Invoice", invoice_name)
		if cint(submit) and payment.docstatus == 0:
			result = submit_supplier_payment(payment.name, str(payment.modified), profile)
			return {**result, "idempotent_replay": True}
		return {**_payment_result(payment, invoice), "idempotent_replay": True}
	invoice = _get_payable_invoice(invoice_name, profile, company, lock=True)
	amount = _validate_payment_amount(amount, invoice.outstanding_amount)
	frappe.db.savepoint("posnext_supplier_payment")
	try:
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		payment = get_payment_entry("Purchase Invoice", invoice.name, party_amount=amount, bank_account=resolved_from, payment_type="Pay", reference_date=reference_date)
		payment.update({
			"posting_date": posting_date,
			"reference_date": reference_date,
			"mode_of_payment": mode_of_payment,
			"reference_no": reference_no,
			"remarks": remarks,
			"paid_from": resolved_from,
			"custom_posnext_pos_profile": profile,
			"custom_posnext_idempotency_key": key,
			"custom_posnext_request_fingerprint": fingerprint,
		})
		remaining = amount
		for row in payment.references:
			if row.reference_doctype != "Purchase Invoice" or row.reference_name != invoice.name:
				row.allocated_amount = 0
				continue
			row.allocated_amount = min(flt(row.outstanding_amount), remaining)
			remaining -= row.allocated_amount
		if remaining > AMOUNT_TOLERANCE:
			frappe.throw(_("Unable to allocate the full payment amount"))
		payment.set_amounts()
		payment.insert(ignore_permissions=False)
		if cint(submit):
			invoice = _get_payable_invoice(invoice_name, profile, company, lock=True)
			_validate_payment_amount(amount, invoice.outstanding_amount)
			payment.submit()
		return {**_payment_result(payment, invoice), "idempotent_replay": False}
	except frappe.UniqueValidationError:
		frappe.db.rollback(save_point="posnext_supplier_payment")
		existing = frappe.db.get_value("Payment Entry", {"custom_posnext_idempotency_key": key}, "name")
		if existing:
			payment = assert_doc_permission("Payment Entry", existing)
			_assert_profile_document(payment, profile, company)
			_assert_request_fingerprint(payment, fingerprint, "supplier payment")
			return {**_payment_result(payment, assert_doc_permission("Purchase Invoice", invoice_name)), "idempotent_replay": True}
		raise
	except Exception:
		frappe.db.rollback(save_point="posnext_supplier_payment")
		raise


def _get_supplier_payment(name, profile, company, ptype="read"):
	payment = assert_doc_permission("Payment Entry", name, ptype)
	_assert_profile_document(payment, profile, company)
	if payment.party_type != "Supplier" or payment.payment_type != "Pay":
		frappe.throw(_("This payment is not a supplier payment"))
	return payment


@frappe.whitelist()
def submit_supplier_payment(name, expected_modified, pos_profile=None):
	profile, company = _context("supplier_payments", pos_profile)
	frappe.has_permission("Payment Entry", "submit", throw=True)
	locked = lock_document("Payment Entry", name, ["name", "modified", "docstatus"])
	payment = _get_supplier_payment(name, profile, company, "submit")
	if payment.docstatus != 0:
		frappe.throw(_("Only draft payments can be submitted"))
	if str(locked.modified) != str(expected_modified or ""):
		frappe.throw(_("This payment changed after you opened it. Reload before submitting."), frappe.TimestampMismatchError)
	refs = [row for row in payment.references if row.reference_doctype == "Purchase Invoice" and flt(row.allocated_amount) > 0]
	if len(refs) != 1:
		frappe.throw(_("A supplier payment must allocate exactly one Purchase Invoice"))
	invoice = _get_payable_invoice(refs[0].reference_name, profile, company, lock=True)
	_validate_payment_amount(refs[0].allocated_amount, invoice.outstanding_amount)
	payment.submit()
	return _payment_result(payment, invoice)


@frappe.whitelist()
def cancel_supplier_payment(name, pos_profile=None):
	profile, company = _context("supplier_payments", pos_profile)
	frappe.has_permission("Payment Entry", "cancel", throw=True)
	lock_document("Payment Entry", name)
	payment = _get_supplier_payment(name, profile, company, "cancel")
	if payment.docstatus != 1:
		frappe.throw(_("Only submitted payments can be cancelled"))
	for row in payment.references:
		if row.reference_doctype == "Purchase Invoice":
			lock_document("Purchase Invoice", row.reference_name)
	payment.cancel()
	return _payment_result(payment)


@frappe.whitelist()
def get_supplier_payments(supplier=None, from_date=None, to_date=None, limit=50, start=0, pos_profile=None):
	profile, company = _context("supplier_payments", pos_profile)
	frappe.has_permission("Payment Entry", "read", throw=True)
	filters = {"party_type": "Supplier", "payment_type": "Pay", "company": company, "custom_posnext_pos_profile": profile}
	if supplier:
		filters["party"] = supplier
	if from_date and to_date:
		filters["posting_date"] = ["between", [getdate(from_date), getdate(to_date)]]
	elif from_date:
		filters["posting_date"] = [">=", getdate(from_date)]
	elif to_date:
		filters["posting_date"] = ["<=", getdate(to_date)]
	fields = ["name", "posting_date", "party", "party_name", "company", "paid_amount", "paid_from_account_currency", "mode_of_payment", "reference_no", "docstatus", "paid_from", "remarks", "modified"]
	rows = frappe.get_list("Payment Entry", filters=filters, fields=fields, order_by="posting_date desc, creation desc", limit=min(cint(limit), 100), start=cint(start))
	payment_names = [row.name for row in rows]
	allocations_by_payment = {name: [] for name in payment_names}
	if payment_names:
		allocations = frappe.get_all(
			"Payment Entry Reference",
			filters={
				"parent": ["in", payment_names],
				"reference_doctype": "Purchase Invoice",
			},
			fields=["parent", "reference_name", "allocated_amount", "outstanding_amount"],
			order_by="idx asc",
			limit=0,
		)
		for allocation in allocations:
			allocations_by_payment[allocation.parent].append(allocation)
	for row in rows:
		row["allocations"] = allocations_by_payment[row.name]
	total = len(frappe.get_list("Payment Entry", filters=filters, pluck="name", limit=0))
	return {"payments": rows, "total": total}


@frappe.whitelist()
def get_purchase_outstanding_summary(supplier=None, from_date=None, to_date=None, pos_profile=None):
	profile, company = _context("purchases", pos_profile)
	filters = {"docstatus": 1, "company": company, "custom_posnext_pos_profile": profile}
	if supplier:
		filters["supplier"] = supplier
	if from_date and to_date:
		filters["posting_date"] = ["between", [getdate(from_date), getdate(to_date)]]
	elif from_date:
		filters["posting_date"] = [">=", getdate(from_date)]
	elif to_date:
		filters["posting_date"] = ["<=", getdate(to_date)]
	rows = frappe.get_list("Purchase Invoice", filters=filters, fields=["grand_total", "outstanding_amount", "status"], limit=0)
	outstanding = sum(max(flt(row.outstanding_amount), 0) for row in rows)
	return {
		"total_outstanding": outstanding,
		"invoice_count": len(rows),
		"unpaid_count": sum(flt(row.outstanding_amount) >= flt(row.grand_total) - AMOUNT_TOLERANCE for row in rows),
		"partial_count": sum(AMOUNT_TOLERANCE < flt(row.outstanding_amount) < flt(row.grand_total) - AMOUNT_TOLERANCE for row in rows),
		"paid_count": sum(flt(row.outstanding_amount) <= AMOUNT_TOLERANCE for row in rows),
	}
