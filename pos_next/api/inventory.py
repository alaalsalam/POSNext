"""Safe POS context for ERPNext's native Stock Reconciliation screen."""

import frappe
from frappe import _

from pos_next.api.feature_flags import resolve_pos_profile


@frappe.whitelist()
def get_stock_reconciliation_context(pos_profile=None):
	"""Return only the company and warehouse authorized by the active POS Profile."""
	frappe.has_permission("Stock Reconciliation", "create", throw=True)
	profile = resolve_pos_profile(pos_profile=pos_profile)
	context = frappe.db.get_value("POS Profile", profile, ["company", "warehouse"], as_dict=True)
	if not context or not context.warehouse:
		frappe.throw(_("The POS Profile must have a warehouse before inventory can be adjusted."))
	return {"pos_profile": profile, "company": context.company, "warehouse": context.warehouse}
