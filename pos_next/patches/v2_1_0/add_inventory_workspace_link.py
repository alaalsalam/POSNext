"""Expose the native stock count screen in the POS workspace."""

import frappe


def execute():
	if not frappe.db.exists("Workspace", "POS"):
		return
	workspace = frappe.get_doc("Workspace", "POS")
	if any(row.link_to == "Stock Reconciliation" for row in workspace.links):
		return
	workspace.append(
		"links",
		{
			"type": "Link",
			"label": "جرد وتسوية المخزون",
			"link_type": "DocType",
			"link_to": "Stock Reconciliation",
		},
	)
	workspace.save(ignore_permissions=True)
