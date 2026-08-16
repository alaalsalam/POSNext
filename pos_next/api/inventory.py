"""Safe POS context for ERPNext's native Stock Reconciliation screen."""

import frappe
from frappe import _

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
