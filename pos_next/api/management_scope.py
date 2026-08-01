"""Shared security and scope checks for manager-only POS capabilities."""

import re

import frappe
from frappe import _
from frappe.utils import cint

from pos_next.api.feature_flags import is_feature_manager, require_feature

IDEMPOTENCY_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,139}$")


def require_manager_feature(feature, pos_profile=None, company=None):
	"""Require a profile flag and an authorized management role."""
	profile = require_feature(feature, pos_profile=pos_profile, company=company)
	if not is_feature_manager():
		frappe.throw(_("Only an authorized POS manager can use this feature"), frappe.PermissionError)
	profile_company = frappe.db.get_value("POS Profile", profile, "company")
	if not frappe.has_permission("Company", "read", doc=profile_company):
		frappe.throw(_("You do not have access to this company"), frappe.PermissionError)
	return profile, profile_company


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
