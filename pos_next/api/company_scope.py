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
SHARED_STRUCTURAL_ROOTS = {
	"Item Group": "All Item Groups",
	"Customer Group": "All Customer Groups",
	"Supplier Group": "All Supplier Groups",
}


def is_multi_company_site():
	return frappe.db.get_single_value("POS Branding Settings", "tenant_mode") == "Multiple Companies"


def active_company(user=None):
	"""Return a company only when it is a valid native Frappe default."""
	user = user or frappe.session.user
	selected_company = None
	if hasattr(frappe, "session") and hasattr(frappe.session, "selected_company"):
		selected_company = frappe.session.get("selected_company")
	if not selected_company and hasattr(frappe, "session") and hasattr(frappe.session, "data"):
		selected_company = getattr(frappe.session.data, "selected_company", None)

	if selected_company and frappe.db.exists("Company", selected_company):
		if frappe.has_permission("Company", "read", doc=selected_company, user=user):
			return selected_company

	# Prefer the user's custom POS company when set in profile.
	if frappe.db.has_column("User", USER_COMPANY_FIELD):
		profile_company = frappe.db.get_value("User", user, USER_COMPANY_FIELD)
		if profile_company and frappe.db.exists("Company", profile_company):
			if frappe.has_permission("Company", "read", doc=profile_company, user=user):
				return profile_company

	company = frappe.defaults.get_user_default("Company", user=user)
	if company and frappe.db.exists("Company", company):
		if frappe.has_permission("Company", "read", doc=company, user=user):
			return company

	permissions = frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": "Company"},
		fields=["for_value"],
		order_by="is_default desc, creation asc",
		limit=1,
	)
	for permission in permissions:
		if permission.for_value and frappe.db.exists("Company", permission.for_value):
			if frappe.has_permission("Company", "read", doc=permission.for_value, user=user):
				return permission.for_value
	return None


def company_query_condition(user, doctype):
	"""Fail closed for company-owned POS masters when multi-company is enabled."""
	if not is_multi_company_site() or doctype not in OWNED_DOCTYPES or not frappe.db.has_column(doctype, OWNERSHIP_FIELD):
		return ""
	company = active_company(user)
	if not company:
		return "1=0"
	condition = f"`tab{doctype}`.`{OWNERSHIP_FIELD}` = {frappe.db.escape(company)}"
	# ERPNext needs these root nodes to create a company-owned child group. They
	# carry no commercial data and are the sole shared structural exception.
	if root := SHARED_STRUCTURAL_ROOTS.get(doctype):
		condition = f"({condition} OR `tab{doctype}`.`name` = {frappe.db.escape(root)})"
	return condition


def enforce_company_ownership(doc, method=None):
	"""Assign the active company on create and block cross-company edits."""
	if not is_multi_company_site() or doc.doctype not in OWNED_DOCTYPES or not frappe.db.has_column(doc.doctype, OWNERSHIP_FIELD):
		return
	# Internal POS provisioning may create a company-owned master while an
	# administrator is setting up another company.  This request-local flag is
	# only set by trusted server-side setup code; it is never read from input.
	company = getattr(frappe.flags, "pos_next_setup_company", None) or active_company()
	doc_company = doc.get(OWNERSHIP_FIELD)

	# During import, allow the row-level company to be authoritative when no
	# active company has been selected yet.
	if not company and getattr(frappe.flags, "in_import", False):
		if doc_company and frappe.db.exists("Company", doc_company):
			if frappe.has_permission("Company", "read", doc=doc_company):
				company = doc_company
		elif doc.name and not doc.is_new():
			persisted_company = frappe.db.get_value(doc.doctype, doc.name, OWNERSHIP_FIELD)
			if persisted_company and frappe.db.exists("Company", persisted_company):
				if frappe.has_permission("Company", "read", doc=persisted_company):
					company = persisted_company

	if not company:
		frappe.throw(_("Select an allowed company before creating or editing POS master data."), frappe.PermissionError)

	if doc_company and doc_company != company:
		frappe.throw(_("This record belongs to a different company."), frappe.PermissionError)
	doc.set(OWNERSHIP_FIELD, company)


def assert_company_ownership(doctype, name):
	"""Reject direct reads of a POS master belonging to another company."""
	if not is_multi_company_site() or doctype not in OWNED_DOCTYPES or not frappe.db.has_column(doctype, OWNERSHIP_FIELD):
		return
	company = active_company()
	owner = frappe.db.get_value(doctype, name, OWNERSHIP_FIELD)
	if name == SHARED_STRUCTURAL_ROOTS.get(doctype):
		return
	if not company or not owner or owner != company:
		frappe.throw(_("This record is not available for the active company."), frappe.PermissionError)


def has_company_document_permission(doc, user=None, permission_type=None):
	"""Document-level guard for direct URLs and APIs that bypass list filters."""
	if not is_multi_company_site() or doc.doctype not in OWNED_DOCTYPES:
		return None
	if doc.is_new():
		return None  # validate assigns the owner and requires an active company.
	if doc.name == SHARED_STRUCTURAL_ROOTS.get(doc.doctype):
		return True
	company = active_company(user)
	return bool(company and doc.get(OWNERSHIP_FIELD) == company)


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
	# Exactly one native Company User Permission is the default.  Keeping old
	# permissions is intentional: an administrator may grant a user extra
	# companies later, but the selected POS Company remains deterministic.
	frappe.db.set_value(
		"User Permission", {"user": doc.name, "allow": "Company"}, "is_default", 0, update_modified=False
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
