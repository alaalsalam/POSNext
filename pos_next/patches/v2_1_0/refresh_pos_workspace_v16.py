"""Apply the English-first POS workspace design to existing sites."""

import json

import frappe
from frappe.desk.doctype.desktop_icon.desktop_icon import add_workspace_to_desktop, clear_desktop_icons_cache


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

	# Replace the old, manually-created desktop entry with a direct entry point
	# to the canonical POS workspace on Frappe v16's apps screen.
	frappe.delete_doc_if_exists("Desktop Icon", "POS Awesome", force=True)
	frappe.delete_doc_if_exists("Workspace Sidebar", "POS Awesome", force=True)
	add_workspace_to_desktop("POS")
	pos_icon = frappe.get_doc("Desktop Icon", "POS")
	pos_icon.icon = "sell"
	pos_icon.bg_color = "blue"
	pos_icon.save(ignore_permissions=True)
	clear_desktop_icons_cache()
	frappe.clear_cache()
