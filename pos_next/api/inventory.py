"""Safe POS context for ERPNext's native Stock Reconciliation screen."""

import frappe
from frappe import _
from frappe.utils import flt, nowdate

from pos_next.api.feature_flags import resolve_pos_profile
from pos_next.api.company_scope import assert_company_ownership, is_multi_company_site


@frappe.whitelist()
def get_stock_reconciliation_context(pos_profile=None):
	"""Return only the company and warehouse authorized by the active POS Profile."""
	frappe.has_permission("Stock Reconciliation", "create", throw=True)
	profile = resolve_pos_profile(pos_profile=pos_profile)
	context = frappe.db.get_value("POS Profile", profile, ["company", "warehouse"], as_dict=True)
	if not context or not context.warehouse:
		frappe.throw(_("The POS Profile must have a warehouse before inventory can be adjusted."))
	return {"pos_profile": profile, "company": context.company, "warehouse": context.warehouse}


@frappe.whitelist()
def submit_pos_stock_reconciliation(pos_profile=None, purpose="Stock Reconciliation", posting_date=None, rows=None):
	"""Submit a company-scoped inventory count from the POS interface.

	The POS never accepts a company, warehouse or price list from the browser.
	They are resolved from the assigned POS Profile, then the native ERPNext
	Stock Reconciliation document performs the stock and accounting posting.
	"""
	frappe.has_permission("Stock Reconciliation", "create", throw=True)
	profile = resolve_pos_profile(pos_profile=pos_profile)
	context = frappe.db.get_value("POS Profile", profile, ["company", "warehouse"], as_dict=True)
	if not context or not context.warehouse:
		frappe.throw(_("The POS Profile must have a warehouse before inventory can be adjusted."))

	if purpose not in ("Opening Stock", "Stock Reconciliation"):
		frappe.throw(_("Invalid inventory adjustment type."))
	if isinstance(rows, str):
		rows = frappe.parse_json(rows)
	if not isinstance(rows, list) or not rows:
		frappe.throw(_("Add at least one item before submitting the inventory adjustment."))

	doc = frappe.new_doc("Stock Reconciliation")
	doc.company = context.company
	doc.set_warehouse = context.warehouse
	doc.custom_pos_profile = profile
	doc.purpose = purpose
	doc.posting_date = posting_date or nowdate()

	seen_items = set()
	for raw in rows:
		item_code = (raw.get("item_code") or "").strip()
		if not item_code or not frappe.db.exists("Item", item_code):
			frappe.throw(_("Select a valid item for every row."))
		if item_code in seen_items:
			frappe.throw(_("Item {0} was entered more than once.").format(item_code))
		seen_items.add(item_code)
		if is_multi_company_site():
			assert_company_ownership("Item", item_code)

		qty = flt(raw.get("qty"))
		if qty < 0:
			frappe.throw(_("Counted quantity cannot be negative."))
		buying_rate = flt(raw.get("buying_rate"))
		selling_rate = flt(raw.get("selling_rate"))
		doc.append("items", {
			"item_code": item_code,
			"warehouse": context.warehouse,
			"qty": qty,
			# The buying rate is the valuation rate used by the stock ledger.
			"valuation_rate": buying_rate,
			"custom_pos_buying_rate": buying_rate,
			"custom_pos_selling_rate": selling_rate,
		})

	doc.insert()
	doc.submit()
	return {"name": doc.name, "message": _("Inventory adjustment submitted successfully.")}


def validate_stock_reconciliation_context(doc, method=None):
	"""Protect POS-originated reconciliations from a forged profile/company."""
	profile = doc.get("custom_pos_profile")
	if not profile:
		if any(row.get("custom_pos_buying_rate") or row.get("custom_pos_selling_rate") for row in doc.items):
			frappe.throw(_("A POS Profile is required when saving prices from inventory reconciliation."))
		return
	resolve_pos_profile(pos_profile=profile, company=doc.company)


def sync_reconciliation_prices(doc, method=None):
	"""Persist optional buying and selling rates after a submitted stock count."""
	profile = doc.get("custom_pos_profile")
	if not profile:
		return
	validate_stock_reconciliation_context(doc)
	selling_price_list = frappe.db.get_value("POS Profile", profile, "selling_price_list")
	buying_price_list = frappe.db.get_single_value("Buying Settings", "buying_price_list")
	for row in doc.items:
		if is_multi_company_site():
			assert_company_ownership("Item", row.item_code)
		if row.get("custom_pos_buying_rate"):
			_upsert_item_price(row.item_code, buying_price_list, row.custom_pos_buying_rate, row.stock_uom)
		if row.get("custom_pos_selling_rate"):
			_upsert_item_price(row.item_code, selling_price_list, row.custom_pos_selling_rate, row.stock_uom)


def _upsert_item_price(item_code, price_list, rate, uom):
	if not price_list:
		frappe.throw(_("The required price list is not configured."))
	price = frappe.db.get_value("Item Price", {"item_code": item_code, "price_list": price_list, "uom": uom}, "name")
	if price:
		doc = frappe.get_doc("Item Price", price)
		doc.price_list_rate = rate
		doc.save(ignore_permissions=False)
		return
	currency = frappe.db.get_value("Price List", price_list, "currency")
	frappe.get_doc({"doctype": "Item Price", "item_code": item_code, "price_list": price_list, "price_list_rate": rate, "uom": uom, "currency": currency}).insert(ignore_permissions=False)
