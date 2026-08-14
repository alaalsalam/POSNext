# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

"""Authorization shared by the in-POS dashboard and the five Desk reports."""

import frappe
from frappe import _

from pos_next.api.feature_flags import get_feature_flags, require_feature


def is_report_manager(user=None):
	"""Native report permission is the only report-access authority."""
	return bool(frappe.has_permission("Sales Invoice", "report", user=user))


def assert_report_manager(reference_doctype="Sales Invoice"):
	"""Require native report and read permission for the report's source DocType."""
	if not frappe.has_permission(reference_doctype, "read") or not frappe.has_permission(reference_doctype, "report"):
		frappe.throw(_("You do not have permission to view this POS report"), frappe.PermissionError)


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
