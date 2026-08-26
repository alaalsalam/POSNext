"""Mark POS-created expense accounts.

The Expense Types screen's account picker should only show expense accounts the admin created
FROM that screen — not the whole chart of accounts. This adds a marker field on Account and
grandfathers any account already referenced by an existing POS Expense Type, so configured types
keep resolving.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Account": [
				{
					"fieldname": "custom_pos_expense_account",
					"label": "POS Expense Account",
					"fieldtype": "Check",
					"insert_after": "account_type",
					"default": "0",
					"read_only": 1,
				}
			]
		}
	)

	# Grandfather accounts already used by existing POS Expense Types so nothing already
	# configured disappears from the picker.
	used = list({a for a in frappe.get_all("POS Expense Type", pluck="expense_account") if a})
	if used:
		frappe.db.set_value(
			"Account", {"name": ["in", used]}, "custom_pos_expense_account", 1, update_modified=False
		)
