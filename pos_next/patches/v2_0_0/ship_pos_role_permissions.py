# App-owned permission grants for POS Next's roles (POSNext Cashier / POS Manager)
# on the core ERPNext doctypes the POS relies on. Shipped so a fresh install has a
# working, self-documenting permission model without manual setup — instead of the
# grants living only as ad-hoc site data.
#
# Uses frappe.permissions.add_permission (which snapshots a doctype's standard perms
# into Custom DocPerm before adding a role, preserving every existing role) so this is
# NON-destructive and idempotent — it never removes another role's access, and re-runs
# are a no-op. The app's own doctypes (POS Coupon, POS Settings, POS Opening/Closing
# Shift, POS Offer, Referral Code) already ship their perms in their doctype JSON and
# are intentionally not touched here.

import frappe
from frappe.permissions import add_permission, update_permission_property

# {doctype: [{"role": ..., "<ptype>": 1, ...}]} — reproduces the existing contract exactly.
ROLE_PERMISSIONS = {
 "Item": [
  {
   "role": "POS Manager",
   "read": 1,
   "write": 1,
   "create": 1,
   "report": 1,
   "export": 1,
   "select": 1
  },
  {
   "role": "POSNext Cashier",
   "read": 1,
   "report": 1,
   "select": 1
  }
 ],
 "Sales Invoice": [
  {
   "role": "POS Manager",
   "read": 1,
   "write": 1,
   "create": 1,
   "submit": 1,
   "cancel": 1,
   "amend": 1,
   "report": 1,
   "export": 1,
   "print": 1,
   "email": 1,
   "share": 1
  },
  {
   "role": "POSNext Cashier",
   "read": 1,
   "write": 1,
   "create": 1,
   "submit": 1,
   "cancel": 1,
   "amend": 1,
   "report": 1,
   "export": 1,
   "print": 1
  }
 ],
 "Purchase Invoice": [
  {
   "role": "POS Manager",
   "read": 1,
   "write": 1,
   "create": 1,
   "submit": 1,
   "cancel": 1,
   "report": 1,
   "print": 1,
   "email": 1
  }
 ],
 "Payment Entry": [
  {
   "role": "POS Manager",
   "read": 1,
   "write": 1,
   "create": 1,
   "submit": 1,
   "cancel": 1,
   "report": 1,
   "export": 1,
   "print": 1,
   "email": 1
  },
  {
   "role": "POSNext Cashier",
   "read": 1,
   "write": 1,
   "create": 1,
   "submit": 1,
   "export": 1
  }
 ],
 "Promotional Scheme": [
  {
   "role": "POS Manager",
   "read": 1,
   "write": 1,
   "create": 1,
   "delete": 1,
   "report": 1,
   "export": 1,
   "print": 1,
   "email": 1,
   "share": 1
  },
  {
   "role": "POSNext Cashier",
   "read": 1
  }
 ],
 "POS Profile": [
  {
   "role": "POS Manager",
   "read": 1,
   "write": 1,
   "report": 1
  },
  {
   "role": "POSNext Cashier",
   "read": 1,
   "export": 1
  }
 ],
 "Customer": [
  {
   "role": "POS Manager",
   "read": 1,
   "write": 1,
   "create": 1,
   "report": 1,
   "export": 1,
   "print": 1,
   "email": 1,
   "select": 1
  },
  {
   "role": "POSNext Cashier",
   "read": 1,
   "write": 1,
   "create": 1,
   "report": 1,
   "export": 1,
   "print": 1,
   "select": 1
  }
 ],
 "Supplier": [
  {
   "role": "POS Manager",
   "read": 1,
   "write": 1,
   "create": 1,
   "report": 1
  }
 ],
 "Company": [
  {
   "role": "POS Manager",
   "read": 1,
   "report": 1
  }
 ],
 "Warehouse": [
  {
   "role": "POS Manager",
   "read": 1,
   "report": 1,
   "select": 1
  },
  {
   "role": "POSNext Cashier",
   "read": 1,
   "report": 1,
   "select": 1
  }
 ],
 "Mode of Payment": [
  {
   "role": "POS Manager",
   "read": 1
  }
 ],
 "Item Price": [
  {
   "role": "POS Manager",
   "read": 1,
   "write": 1,
   "create": 1,
   "report": 1
  }
 ]
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
			# Ensure a Custom DocPerm exists for this role (snapshots standard perms first
			# time a doctype is customized, so no ERPNext role loses access).
			add_permission(doctype, role, 0)
			for ptype, value in row.items():
				if ptype == "role":
					continue
				update_permission_property(doctype, role, 0, ptype, value, validate=False)
		validate_permissions_for_doctype(doctype)
