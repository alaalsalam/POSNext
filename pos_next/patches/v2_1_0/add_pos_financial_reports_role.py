"""Provision the owner-only financial reports role."""

import frappe


def execute():
	role = "POS Financial Reports"
	if not frappe.db.exists("Role", role):
		frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)

	admin = frappe.get_doc("User", "Administrator")
	if not any(row.role == role for row in admin.roles):
		admin.append("roles", {"role": role})
		admin.save(ignore_permissions=True)
