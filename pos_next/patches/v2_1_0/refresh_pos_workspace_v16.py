"""Apply the English-first POS workspace design to existing sites."""

import json

import frappe


def execute():
	# A legacy workspace belonging to this app is safe to remove; the canonical
	# workspace is always named POS.  Never touch ERPNext's own workspaces.
	for name in frappe.get_all("Workspace", filters={"module": "POS Next", "name": ["!=", "POS"]}, pluck="name"):
		frappe.delete_doc("Workspace", name, force=True, ignore_permissions=True)

	if not frappe.db.exists("Workspace", "POS"):
		return

	path = frappe.get_app_path("pos_next", "pos_next", "workspace", "pos", "pos.json")
	with open(path, encoding="utf-8") as handle:
		source = json.load(handle)

	workspace = frappe.get_doc("Workspace", "POS")
	workspace.label = source["label"]
	workspace.title = source["title"]
	workspace.icon = source["icon"]
	workspace.indicator_color = source["indicator_color"]
	workspace.content = source["content"]

	# The workspace is app-owned, so replace its navigation atomically from the
	# source definition. This removes stale old-POS entries and adds new screens.
	workspace.set("links", source["links"])
	workspace.set("shortcuts", source["shortcuts"])
	workspace.save(ignore_permissions=True)
	frappe.clear_cache()
