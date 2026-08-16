"""Safe company ownership for POS master data in multi-company sites."""

import frappe
from frappe import _


OWNERSHIP_FIELD = "custom_pos_company"
# These masters do not have ERPNext's native ``company`` field.  Their POS
# ownership is explicit so the standard Desk, Link fields, and POS APIs all
# share one company boundary.  Transactional doctypes keep using their native
# company field and Frappe's Company User Permission.
OWNED_DOCTYPES = (
	"Item",
	"Item Group",
	"Brand",
	"Customer",
	"Customer Group",
	"Supplier",
	"Supplier Group",
)
USER_COMPANY_FIELD = "custom_pos_company"


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


def assert_company_ownership(doctype, name):
	"""Reject direct reads of a POS master belonging to another company."""
	if not is_multi_company_site() or doctype not in OWNED_DOCTYPES or not frappe.db.has_column(doctype, OWNERSHIP_FIELD):
		return
	company = active_company()
	owner = frappe.db.get_value(doctype, name, OWNERSHIP_FIELD)
	if not company or not owner or owner != company:
		frappe.throw(_("This record is not available for the active company."), frappe.PermissionError)


def prepare_user_company(doc, method=None):
	"""Make a new user's selected POS company the native Frappe company context."""
	if not is_multi_company_site() or doc.name in {"Administrator", "Guest"}:
		return
	if not frappe.db.has_column("User", USER_COMPANY_FIELD):
		return
	company = doc.get(USER_COMPANY_FIELD) or active_company()
	if not company:
		frappe.throw(_("Select a POS Company when creating a user in multiple-company mode."), frappe.ValidationError)
	if not frappe.db.exists("Company", company) or not frappe.has_permission("Company", "read", doc=company):
		frappe.throw(_("You cannot assign this POS Company."), frappe.PermissionError)
	doc.set(USER_COMPANY_FIELD, company)


def sync_user_company_permission(doc, method=None):
	"""Create/update the user's default native Company User Permission."""
	if not is_multi_company_site() or doc.name in {"Administrator", "Guest"}:
		return
	company = doc.get(USER_COMPANY_FIELD)
	if not company:
		return
	permission = frappe.db.get_value(
		"User Permission", {"user": doc.name, "allow": "Company", "for_value": company}, "name"
	)
	if permission:
		frappe.db.set_value("User Permission", permission, "is_default", 1, update_modified=False)
	else:
		frappe.get_doc(
			{
				"doctype": "User Permission",
				"user": doc.name,
				"allow": "Company",
				"for_value": company,
				"is_default": 1,
				"apply_to_all_doctypes": 1,
			}
		).insert(ignore_permissions=True)
	frappe.defaults.set_user_default("Company", company, user=doc.name)
