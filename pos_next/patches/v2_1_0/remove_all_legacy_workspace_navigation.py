"""Remove all remaining legacy workspace navigation customizations."""

import frappe


LEGACY_WORKSPACES = ("ERPNext Integrations",)
LEGACY_SIDEBARS = ("ERPNext Integrations", "Selling.")
LEGACY_DESKTOP_ICONS = ("ERPNext Integrations", "Selling.", "Payables", "Receivables")


def execute():
	for name in LEGACY_DESKTOP_ICONS:
		frappe.delete_doc_if_exists("Desktop Icon", name, force=True)

	for name in LEGACY_SIDEBARS:
		frappe.delete_doc_if_exists("Workspace Sidebar", name, force=True)

	for name in LEGACY_WORKSPACES:
		frappe.delete_doc_if_exists("Workspace", name, force=True)

	frappe.clear_cache()
