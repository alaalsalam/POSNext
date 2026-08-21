"""Remove the legacy custom Tools workspace.

The workspace is not owned by an installed application and has no standard
Frappe or ERPNext desktop entry.  Keep this intentionally narrow so standard
and app-provided workspaces are never affected.
"""

import frappe


def execute():
	for doctype in ("Desktop Icon", "Workspace Sidebar", "Workspace"):
		frappe.delete_doc_if_exists(doctype, "Tools", force=True)

	frappe.clear_cache()
