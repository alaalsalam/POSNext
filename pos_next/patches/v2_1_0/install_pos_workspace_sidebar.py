"""Install the app-owned POS navigation sidebar and desktop icon."""

import json
from pathlib import Path

import frappe
from frappe.desk.doctype.desktop_icon.desktop_icon import clear_desktop_icons_cache
from frappe.modules.import_file import import_file_by_path


def execute():
	app_path = Path(frappe.get_app_path("pos_next"))
	for relative_path in ("workspace_sidebar/pos.json", "desktop_icon/pos.json"):
		import_file_by_path(str(app_path / relative_path), force=True, ignore_version=True)

	workspace_source = json.loads((app_path / "pos_next/workspace/pos/pos.json").read_text(encoding="utf-8"))
	workspace = frappe.get_doc("Workspace", "POS")
	workspace.icon = workspace_source["icon"]
	workspace.content = workspace_source["content"]
	workspace.public = workspace_source["public"]
	workspace.set("roles", workspace_source["roles"])
	workspace.save(ignore_permissions=True)

	clear_desktop_icons_cache()
	frappe.clear_cache()
