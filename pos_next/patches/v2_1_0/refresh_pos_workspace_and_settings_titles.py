"""Refresh the shipped POS workspace and backfill readable settings titles."""

import json
from pathlib import Path

import frappe


def execute():
	frappe.db.sql(
		"""
		UPDATE `tabPOS Settings` settings
		INNER JOIN `tabPOS Profile` profile ON profile.name = settings.pos_profile
		SET settings.company = profile.company,
			settings.settings_title = CONCAT('POS Settings · ', profile.company)
		"""
	)
	_refresh_workspace()


def _refresh_workspace():
	workspace_file = Path(frappe.get_app_path("pos_next")) / "pos_next/workspace/pos/pos.json"
	if not workspace_file.exists() or not frappe.db.exists("Workspace", "POS"):
		return

	data = json.loads(workspace_file.read_text(encoding="utf-8"))
	workspace = frappe.get_doc("Workspace", "POS")
	workspace.icon = data["icon"]
	workspace.label = data["label"]
	workspace.title = data["title"]
	workspace.content = data["content"]
	workspace.set("links", data["links"])
	workspace.set("shortcuts", data["shortcuts"])
	workspace.save(ignore_permissions=True)
