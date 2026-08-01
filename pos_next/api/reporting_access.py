# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

"""Authorization shared by the in-POS dashboard and the five Desk reports."""

import frappe
from frappe import _

from pos_next.api.feature_flags import get_feature_flags, require_feature

REPORT_MANAGER_ROLES = {
	"System Manager",
	"Sales Manager",
	"POS Manager",
	"Accounts Manager",
	"Stock Manager",
	"Item Manager",
}


def is_report_manager(user=None):
	roles = set(frappe.get_roles(user or frappe.session.user))
	return bool(roles.intersection(REPORT_MANAGER_ROLES))


def assert_report_manager(reference_doctype="Sales Invoice"):
	"""Require a manager role and normal DocType read permission."""
	if not is_report_manager() or not frappe.has_permission(reference_doctype, "read"):
		frappe.throw(_("Only an authorized manager can view POS reports"), frappe.PermissionError)


def authorize_report(filters=None, reference_doctype="Sales Invoice"):
	"""Authorize one profile-scoped report request and return normalized filters."""
	filters = frappe._dict(filters or {})
	assert_report_manager(reference_doctype)
	if not filters.get("pos_profile"):
		frappe.throw(_("POS Profile is required for this report"), frappe.PermissionError)
	require_feature("pos_reports", pos_profile=filters.pos_profile)
	return filters


def get_reportable_profiles():
	"""Return enabled, assigned profiles whose report flag is on for this user."""
	assert_report_manager()
	user = frappe.session.user
	filters = {"disabled": 0}
	if user != "Administrator":
		assigned = frappe.get_all(
			"POS Profile User", filters={"user": user}, pluck="parent", limit=0
		)
		if not assigned:
			return []
		filters["name"] = ["in", assigned]

	profiles = frappe.get_all(
		"POS Profile",
		filters=filters,
		fields=["name", "company", "currency"],
		order_by="name asc",
		limit=0,
	)
	allowed = []
	for profile in profiles:
		try:
			flags = get_feature_flags(pos_profile=profile.name)
		except frappe.PermissionError:
			continue
		if flags["enable_pos_reports"]:
			allowed.append(profile)
	return allowed
