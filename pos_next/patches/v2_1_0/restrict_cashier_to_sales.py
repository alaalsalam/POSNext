"""Keep the POS Cashier role limited to the sales workflow."""

import frappe


def execute():
	# Cash drawer movements and supplier/customer payments are delegated to the
	# dedicated POS Cash Management role.  Removing the legacy entries is
	# necessary because Frappe combines every permission row for a role.
	for doctype in ("Journal Entry", "Payment Entry"):
		frappe.db.delete("Custom DocPerm", {"parent": doctype, "role": "POS Cashier"})

	frappe.clear_cache()
