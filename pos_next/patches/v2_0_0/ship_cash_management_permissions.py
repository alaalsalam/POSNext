# Cash Management feature: the cashier records drawer cash movements (expense / receipt /
# payment) as a Cash Entry Journal Entry. That needs Journal Entry access for the POS roles,
# which cashiers don't have by default. Grant it the same non-destructive way as
# ship_pos_role_permissions (add_permission snapshots standard perms first, so no ERPNext role
# loses access; idempotent). Cashiers get read/create/submit only — deliberately NO write /
# cancel / amend: a cashier voiding their own cash entries is a fraud vector, so corrections go
# through a manager in Desk.

import frappe
from frappe.permissions import add_permission, update_permission_property

ROLE_PERMISSIONS = {
	"Journal Entry": [
		{
			"role": "POS Manager",
			"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1,
			"amend": 1, "report": 1, "print": 1, "export": 1,
		},
		{
			"role": "POSNext Cashier",
			"read": 1, "create": 1, "submit": 1, "print": 1,
		},
	],
	# Cashier needs to look up an Employee for a "payment to employee" (صرف لموظف) voucher.
	# Customer read already exists (sales); scoped to the cashier's company by the Company UP.
	"Employee": [
		{"role": "POSNext Cashier", "read": 1},
	],
}


def execute():
	from frappe.core.doctype.doctype.doctype import validate_permissions_for_doctype

	for doctype, rows in ROLE_PERMISSIONS.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		for row in rows:
			role = row["role"]
			if not frappe.db.exists("Role", role):
				continue
			add_permission(doctype, role, 0)
			for ptype, value in row.items():
				if ptype == "role":
					continue
				update_permission_property(doctype, role, 0, ptype, value, validate=False)
		validate_permissions_for_doctype(doctype)
