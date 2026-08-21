"""Remove workspaces added by legacy local framework customizations.

These names do not exist in the upstream Frappe/ERPNext version-16 workspace
definitions.  Delete their desk navigation records together with the workspace
so the site retains only upstream-standard and installed-app workspaces.
"""

import frappe


LEGACY_CUSTOM_WORKSPACES = (
	"Accounting.",
	"Custom Users",
	"Financial Management",
	"Reports",
	"Customization",
)


def execute():
	for name in LEGACY_CUSTOM_WORKSPACES:
		for doctype in ("Desktop Icon", "Workspace Sidebar", "Workspace"):
			frappe.delete_doc_if_exists(doctype, name, force=True)

	frappe.clear_cache()
