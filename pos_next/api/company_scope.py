"""Safe company ownership for POS master data in multi-company sites."""

import frappe
from frappe import _


OWNERSHIP_FIELD = "custom_pos_company"
OWNED_DOCTYPES = ("Item", "Item Group", "Customer")


def is_multi_company_site():
	return frappe.db.get_single_value("POS Branding Settings", "tenant_mode") == "Multiple Companies"


def active_company(user=None):
	"""Return a company only when it is a valid native Frappe default."""
	user = user or frappe.session.user
	company = frappe.defaults.get_user_default("Company", user=user)
	if company and frappe.db.exists("Company", company) and frappe.has_permission("Company", "read", doc=company, user=user):
		return company
	permissions = frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": "Company"},
		fields=["for_value"],
		order_by="is_default desc, creation asc",
		limit=1,
	)
	return permissions[0].for_value if permissions else None


def company_query_condition(user, doctype):
	"""Fail closed for company-owned POS masters when multi-company is enabled."""
	if not is_multi_company_site() or doctype not in OWNED_DOCTYPES or not frappe.db.has_column(doctype, OWNERSHIP_FIELD):
		return ""
	company = active_company(user)
	if not company:
		return "1=0"
	return f"`tab{doctype}`.`{OWNERSHIP_FIELD}` = {frappe.db.escape(company)}"


def enforce_company_ownership(doc, method=None):
	"""Assign the active company on create and block cross-company edits."""
	if not is_multi_company_site() or doc.doctype not in OWNED_DOCTYPES or not frappe.db.has_column(doc.doctype, OWNERSHIP_FIELD):
		return
	company = active_company()
	if not company:
		frappe.throw(_("Select an allowed company before creating or editing POS master data."), frappe.PermissionError)
	if doc.get(OWNERSHIP_FIELD) and doc.get(OWNERSHIP_FIELD) != company:
		frappe.throw(_("This record belongs to a different company."), frappe.PermissionError)
	doc.set(OWNERSHIP_FIELD, company)
