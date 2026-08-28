"""Shared security and scope checks for manager-only POS capabilities."""

import re

import frappe
from frappe import _
from frappe.utils import cint

from pos_next.api.feature_flags import require_feature

IDEMPOTENCY_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,139}$")


def require_feature_permission(feature, doctype, ptype="read", pos_profile=None, company=None):
	"""Require a profile feature and its native Frappe DocType permission.

	This is deliberately permission-based rather than role-based.  The role
	assigned in Frappe determines the permission; POS does not maintain a second
	list of privileged role names.
	"""
	profile = require_feature(feature, pos_profile=pos_profile, company=company)
	frappe.has_permission(doctype, ptype, throw=True)
	profile_company = frappe.db.get_value("POS Profile", profile, "company")
	if not frappe.has_permission("Company", "read", doc=profile_company):
		frappe.throw(_("You do not have access to this company"), frappe.PermissionError)
	# The profile is already assignment- and permission-checked in
	# require_feature(). Keep the global query guards on Item/Customer/Supplier
	# masters aligned with that same company for the lifetime of this request.
	frappe.flags.pos_next_company_scope = profile_company
	return profile, profile_company


def require_manager_feature(feature, pos_profile=None, company=None):
	"""Backward-compatible settings-management guard.

	Only POS Settings write permission controls configuration.  Feature modules
	should call :func:`require_feature_permission` with their own DocType.
	"""
	return require_feature_permission(feature, "POS Settings", "write", pos_profile, company)


def assert_doc_permission(doctype, name, ptype="read"):
	"""Load a document and enforce document-level/User Permission access."""
	if not name or not frappe.db.exists(doctype, name):
		frappe.throw(_("{0} was not found").format(_(doctype)))
	doc = frappe.get_doc(doctype, name)
	frappe.has_permission(doctype, ptype, doc=doc, throw=True)
	return doc


def assert_company_resource(doctype, name, company, *, ptype="read", allow_group=False):
	"""Validate a readable company-owned resource."""
	doc = assert_doc_permission(doctype, name, ptype)
	if doc.get("company") != company:
		frappe.throw(_("The selected {0} does not belong to the POS Profile company").format(_(doctype)), frappe.PermissionError)
	if not allow_group and cint(doc.get("is_group")):
		frappe.throw(_("The selected {0} cannot be a group").format(_(doctype)))
	if cint(doc.get("disabled")):
		frappe.throw(_("The selected {0} is disabled").format(_(doctype)))
	return doc


def normalize_idempotency_key(value):
	"""Validate a durable, client-generated retry key."""
	value = (value or "").strip()
	if not IDEMPOTENCY_KEY_RE.fullmatch(value):
		frappe.throw(
			_("Idempotency key must be 8-140 characters using letters, numbers, '.', '_', ':', or '-'")
		)
	return value


def lock_document(doctype, name, fields=None):
	"""Lock a document row until the current database transaction completes."""
	fields = fields or ["name"]
	row = frappe.db.get_value(doctype, name, fields, as_dict=True, for_update=True)
	if not row:
		frappe.throw(_("{0} was not found").format(_(doctype)))
	return row
