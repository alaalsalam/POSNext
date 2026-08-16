"""Install native Frappe roles for POS and migrate the legacy cashier role.

POS permissions intentionally live in Frappe's standard Role / DocPerm model.
This patch only ships initial data; administrators manage the result from Role
Permission Manager and User forms, without a parallel POS permission layer.
"""

import frappe
from frappe.permissions import add_permission, update_permission_property


LEGACY_CASHIER_ROLE = "POSNext Cashier"
POS_CASHIER_ROLE = "POS Cashier"

ROLE_NAMES = (
	"POS Manager",
	POS_CASHIER_ROLE,
	"POS Purchases",
	"POS Expenses",
	"POS Cash Management",
	"POS Reports",
	"POS Catalog Manager",
	"POS Inventory Controller",
)

# Native DocType permissions are the single source of truth.  The frontend and
# API ask Frappe for these permissions; they do not grant access from role names.
ROLE_PERMISSIONS = {
	"POS Manager": {
		"POS Settings": {"read": 1, "write": 1, "create": 1},
		"POS Profile": {"read": 1, "write": 1, "report": 1},
		"Sales Invoice": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "amend": 1, "report": 1, "export": 1, "print": 1},
		"Purchase Invoice": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "report": 1, "print": 1},
		"Payment Entry": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "report": 1, "export": 1, "print": 1},
		"Journal Entry": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "amend": 1, "report": 1, "export": 1, "print": 1},
		"Item": {"read": 1, "write": 1, "create": 1, "report": 1, "export": 1},
		"Item Group": {"read": 1, "write": 1, "create": 1, "report": 1},
		"Item Price": {"read": 1, "write": 1, "create": 1, "report": 1},
		"Customer": {"read": 1, "write": 1, "create": 1, "report": 1},
		"Supplier": {"read": 1, "write": 1, "create": 1, "report": 1},
		"POS Expense Type": {"read": 1, "write": 1, "create": 1, "delete": 1},
		"Stock Reconciliation": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "report": 1, "print": 1},
	},
	POS_CASHIER_ROLE: {
		"POS Profile": {"read": 1},
		"POS Opening Shift": {"read": 1, "write": 1, "create": 1, "submit": 1},
		"POS Closing Shift": {"read": 1, "write": 1, "create": 1, "submit": 1},
		"Sales Invoice": {"read": 1, "write": 1, "create": 1, "submit": 1, "print": 1},
		"Customer": {"read": 1, "write": 1, "create": 1, "select": 1},
		"Item": {"read": 1, "select": 1},
		"Warehouse": {"read": 1, "select": 1},
		# Read-only financial master data is required by ERPNext when a cashier
		# submits a sales invoice and selects a payment method.  It does not grant
		# access to accounting transactions or cash management.
		"Account": {"read": 1},
		"Company": {"read": 1},
		"Cost Center": {"read": 1},
		"Currency": {"read": 1},
		"Mode of Payment": {"read": 1},
		"Price List": {"read": 1},
		"Sales Taxes and Charges Template": {"read": 1},
		"POS Coupon": {"read": 1},
		"Promotional Scheme": {"read": 1},
		"Pricing Rule": {"read": 1},
		"Employee": {"read": 1},
		"POS Expense Type": {"read": 1},
	},
	"POS Purchases": {
		"Purchase Invoice": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "report": 1, "print": 1},
		"Supplier": {"read": 1, "write": 1, "create": 1},
		"Supplier Group": {"read": 1},
		"Payment Entry": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
		"Item": {"read": 1}, "Item Price": {"read": 1}, "Warehouse": {"read": 1},
		"Account": {"read": 1}, "Currency": {"read": 1}, "UOM": {"read": 1},
		"Purchase Taxes and Charges Template": {"read": 1}, "Price List": {"read": 1},
	},
	"POS Expenses": {
		"Journal Entry": {"read": 1, "create": 1, "submit": 1, "print": 1},
		"POS Expense Type": {"read": 1, "write": 1, "create": 1, "delete": 1},
		"Account": {"read": 1}, "Employee": {"read": 1}, "Customer": {"read": 1}, "Supplier": {"read": 1},
	},
	"POS Cash Management": {
		"Journal Entry": {"read": 1, "create": 1, "submit": 1, "print": 1},
		"POS Expense Type": {"read": 1}, "Account": {"read": 1}, "Employee": {"read": 1},
		"Customer": {"read": 1}, "Supplier": {"read": 1},
	},
	"POS Reports": {
		"Sales Invoice": {"read": 1, "report": 1}, "Purchase Invoice": {"read": 1, "report": 1},
		"Payment Entry": {"read": 1, "report": 1}, "Journal Entry": {"read": 1, "report": 1},
		"Item": {"read": 1, "report": 1},
	},
	"POS Catalog Manager": {
		"Item": {"read": 1, "write": 1, "create": 1, "report": 1, "export": 1},
		"Item Group": {"read": 1, "write": 1, "create": 1, "report": 1},
		"Item Price": {"read": 1, "write": 1, "create": 1, "report": 1},
		"Brand": {"read": 1}, "UOM": {"read": 1}, "Price List": {"read": 1},
	},
	"POS Inventory Controller": {
		"Stock Reconciliation": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "report": 1, "print": 1},
		"Item": {"read": 1}, "Warehouse": {"read": 1}, "Company": {"read": 1},
		"UOM": {"read": 1}, "Batch": {"read": 1}, "Serial No": {"read": 1},
		"Account": {"read": 1}, "Cost Center": {"read": 1},
		"Item Price": {"read": 1, "write": 1, "create": 1},
	},
}


def _ensure_roles():
	for role_name in ROLE_NAMES:
		if not frappe.db.exists("Role", role_name):
			frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(
				ignore_permissions=True
			)


def _migrate_legacy_cashier_role():
	if not frappe.db.exists("Role", LEGACY_CASHIER_ROLE):
		return

	# Roles can be assigned directly to a User or inherited through a Role
	# Profile.  Both are native Frappe assignments and must migrate together.
	for parenttype in ("User", "Role Profile"):
		for parent in frappe.get_all(
			"Has Role", filters={"role": LEGACY_CASHIER_ROLE, "parenttype": parenttype}, pluck="parent"
		):
			owner = frappe.get_doc(parenttype, parent)
			if not any(row.role == POS_CASHIER_ROLE for row in owner.roles):
				owner.append("roles", {"role": POS_CASHIER_ROLE})
			for row in list(owner.roles):
				if row.role == LEGACY_CASHIER_ROLE:
					owner.remove(row)
			owner.save(ignore_permissions=True)

	for legacy_perm in frappe.get_all("Custom DocPerm", filters={"role": LEGACY_CASHIER_ROLE}, pluck="name"):
		doc = frappe.get_doc("Custom DocPerm", legacy_perm)
		if frappe.db.exists("Custom DocPerm", {"parent": doc.parent, "role": POS_CASHIER_ROLE, "permlevel": doc.permlevel}):
			continue
		new_doc = frappe.copy_doc(doc)
		new_doc.role = POS_CASHIER_ROLE
		new_doc.insert(ignore_permissions=True)

	frappe.db.set_value("Role", LEGACY_CASHIER_ROLE, "disabled", 1)


def _apply_permissions():
	from frappe.core.doctype.doctype.doctype import validate_permissions_for_doctype

	for role, doctypes in ROLE_PERMISSIONS.items():
		for doctype, permissions in doctypes.items():
			if not frappe.db.exists("DocType", doctype):
				continue
			add_permission(doctype, role, 0)
			for ptype, value in permissions.items():
				update_permission_property(doctype, role, 0, ptype, value, validate=False)
			validate_permissions_for_doctype(doctype)


def execute():
	_ensure_roles()
	_migrate_legacy_cashier_role()
	_apply_permissions()
	frappe.clear_cache()
