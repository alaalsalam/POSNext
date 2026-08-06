import frappe

# Workspace names this app used to ship under, before they were renamed/replaced by
# workspace/pos/pos.json (name "POS"). v1_7_0.reinstall_workspace was meant to delete these
# on upgrade, but never ran successfully because of a bug in its JSON-loading helper (fixed
# separately) — Frappe patches are one-shot, so sites that already "ran" the broken version
# won't retry it just because the code changed. This patch does the cleanup explicitly.
LEGACY_WORKSPACE_NAMES = ["POSNext"]


def execute():
	for workspace_name in LEGACY_WORKSPACE_NAMES:
		if frappe.db.exists("Workspace", workspace_name):
			frappe.delete_doc("Workspace", workspace_name, force=True, ignore_permissions=True)
