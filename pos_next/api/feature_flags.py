# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

"""Profile-scoped feature flags for management capabilities in Digit POS."""

import frappe
from frappe import _
from frappe.utils import cint

FEATURE_FLAGS = {
	"catalog": "enable_catalog_management",
	"purchases": "enable_purchases",
	"supplier_payments": "enable_supplier_payments",
	"pos_reports": "enable_pos_reports",
	"cash_management": "enable_cash_management",
}

FEATURE_DEPENDENCIES = {
	"enable_supplier_payments": ("enable_purchases",),
}

FEATURE_DEFAULTS = {fieldname: 0 for fieldname in FEATURE_FLAGS.values()}
FEATURE_MANAGER_ROLES = {"System Manager", "Sales Manager", "POS Manager"}


def get_feature_field(feature):
	"""Resolve a public feature key or fieldname to a supported POS Settings field."""
	fieldname = FEATURE_FLAGS.get(feature, feature)
	if fieldname not in FEATURE_DEFAULTS:
		frappe.throw(_("Unknown POS feature: {0}").format(feature))
	return fieldname


def is_feature_manager(user=None):
	"""Return whether the user may control experimental management features."""
	roles = set(frappe.get_roles(user or frappe.session.user))
	return bool(roles.intersection(FEATURE_MANAGER_ROLES))


def assert_feature_manager():
	"""Reject POS Settings mutations from cashiers and other non-manager users."""
	if not is_feature_manager() or not frappe.has_permission("POS Settings", "write"):
		frappe.throw(_("Only an authorized POS manager can change POS Settings"), frappe.PermissionError)


def _get_active_pos_profile():
	return frappe.db.get_value(
		"POS Opening Shift",
		{
			"user": frappe.session.user,
			"docstatus": 1,
			"status": "Open",
			"pos_closing_shift": ["is", "not set"],
		},
		"pos_profile",
		order_by="period_start_date desc",
	)


def assert_profile_access(pos_profile):
	"""Enforce profile assignment plus POS Profile and Company user permissions."""
	user = frappe.session.user
	if user == "Administrator":
		return
	if not frappe.db.exists("POS Profile User", {"parent": pos_profile, "user": user}):
		frappe.throw(_("You do not have access to this POS Profile"), frappe.PermissionError)

	company = frappe.db.get_value("POS Profile", pos_profile, "company")
	if not frappe.has_permission("POS Profile", "read", doc=pos_profile, user=user):
		frappe.throw(_("You do not have access to this POS Profile"), frappe.PermissionError)
	if company and not frappe.has_permission("Company", "read", doc=company, user=user):
		frappe.throw(_("You do not have access to this company"), frappe.PermissionError)


def resolve_pos_profile(pos_profile=None, company=None):
	"""Resolve the explicit or active profile and optionally validate its company."""
	pos_profile = pos_profile or _get_active_pos_profile()
	if not pos_profile or not frappe.db.exists("POS Profile", pos_profile):
		frappe.throw(_("An active POS Profile is required for this feature"), frappe.PermissionError)
	assert_profile_access(pos_profile)

	profile_company = frappe.db.get_value("POS Profile", pos_profile, "company")
	if company and company != profile_company:
		frappe.throw(_("The selected company does not belong to the active POS Profile"), frappe.PermissionError)
	return pos_profile


def get_feature_flags(pos_profile=None, company=None):
	"""Return secure-off feature flags for a POS Profile."""
	pos_profile = resolve_pos_profile(pos_profile=pos_profile, company=company)
	values = frappe.db.get_value(
		"POS Settings",
		{"pos_profile": pos_profile, "enabled": 1},
		list(FEATURE_DEFAULTS),
		as_dict=True,
	)
	flags = FEATURE_DEFAULTS.copy()
	if values:
		flags.update({fieldname: cint(values.get(fieldname)) for fieldname in flags})
	return flags


def validate_feature_dependencies(settings):
	"""Prevent unsafe persisted flag combinations."""
	for feature, dependencies in FEATURE_DEPENDENCIES.items():
		if not cint(settings.get(feature)):
			continue
		for dependency in dependencies:
			if not cint(settings.get(dependency)):
				frappe.throw(
					_("Supplier Payments requires Purchases to be enabled first")
				)


def require_feature(feature, pos_profile=None, company=None):
	"""Enforce a feature flag server-side and return the resolved POS Profile."""
	fieldname = get_feature_field(feature)
	pos_profile = resolve_pos_profile(pos_profile=pos_profile, company=company)
	flags = get_feature_flags(pos_profile=pos_profile)
	if not flags[fieldname]:
		frappe.throw(
			_("This POS feature is disabled for profile {0}").format(pos_profile),
			frappe.PermissionError,
		)
	return pos_profile


def changed_feature_flags(doc):
	"""Return old/new flag values for native Version audit and authorization checks."""
	if doc.is_new():
		return {
			fieldname: {"old": 0, "new": cint(doc.get(fieldname))}
			for fieldname in FEATURE_DEFAULTS
			if cint(doc.get(fieldname))
		}

	previous = doc.get_doc_before_save()
	if not previous:
		return {}
	return {
		fieldname: {"old": cint(previous.get(fieldname)), "new": cint(doc.get(fieldname))}
		for fieldname in FEATURE_DEFAULTS
		if cint(previous.get(fieldname)) != cint(doc.get(fieldname))
	}


def publish_feature_flag_update(doc, changed=None):
	"""Invalidate live POS sessions after the settings transaction commits."""
	changed = changed if changed is not None else changed_feature_flags(doc)
	if not changed:
		return
	frappe.publish_realtime(
		"pos_feature_flags_updated",
		{
			"pos_profile": doc.pos_profile,
			"feature_flags": {field: cint(doc.get(field)) for field in FEATURE_DEFAULTS},
			"changed": changed,
		},
		after_commit=True,
	)
