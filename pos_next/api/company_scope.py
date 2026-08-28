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
USER_ALLOWED_COMPANIES_FIELD = "custom_pos_allowed_companies"
SHARED_STRUCTURAL_ROOTS = {
	"Item Group": "All Item Groups",
	"Customer Group": "All Customer Groups",
	"Supplier Group": "All Supplier Groups",
}


def is_multi_company_site():
	return frappe.db.get_single_value("POS Branding Settings", "tenant_mode") == "Multiple Companies"


def allowed_companies_for_user(user):
	"""Return the explicit POS company boundary for a user.

	The User child table is the source of truth.  The legacy single-company
	field is kept as a compatible default and is automatically folded into the
	list for sites created before the multi-company selector existed.
	"""
	if user in {"Administrator", "Guest"}:
		return []

	companies = []
	if frappe.get_meta("User").has_field(USER_ALLOWED_COMPANIES_FIELD) and frappe.db.exists("DocType", "POS User Company"):
		companies = frappe.get_all(
			"POS User Company",
			filters={"parent": user, "parenttype": "User", "parentfield": USER_ALLOWED_COMPANIES_FIELD},
			pluck="company",
			order_by="idx asc",
			limit_page_length=0,
		)
	default_company = (
		frappe.db.get_value("User", user, USER_COMPANY_FIELD)
		if frappe.db.has_column("User", USER_COMPANY_FIELD)
		else None
	)
	if default_company and default_company not in companies:
		companies.insert(0, default_company)
	return [company for company in dict.fromkeys(companies) if frappe.db.exists("Company", company)]


def _user_allowed_company(user, company):
	"""Administrator is unrestricted; all other users need an explicit grant."""
	return user == "Administrator" or company in allowed_companies_for_user(user)


def active_company(user=None):
	"""Return a company only when it is a valid native Frappe default."""
	user = user or frappe.session.user
	# POS APIs resolve and authorize a POS Profile before setting this request-local
	# context. It makes the global master-data query guard agree with the profile
	# company, including mobile sessions that do not have a Desk company selected.
	request_company = getattr(frappe.flags, "pos_next_company_scope", None)
	if request_company and frappe.db.exists("Company", request_company):
		if _user_allowed_company(user, request_company) and frappe.has_permission("Company", "read", doc=request_company, user=user):
			return request_company
	selected_company = None
	if hasattr(frappe, "session") and hasattr(frappe.session, "selected_company"):
		selected_company = frappe.session.get("selected_company")
	if not selected_company and hasattr(frappe, "session") and hasattr(frappe.session, "data"):
		selected_company = getattr(frappe.session.data, "selected_company", None)

	if selected_company and frappe.db.exists("Company", selected_company):
		if _user_allowed_company(user, selected_company) and frappe.has_permission("Company", "read", doc=selected_company, user=user):
			return selected_company

	# Prefer the user's custom POS company when set in profile.
	if frappe.db.has_column("User", USER_COMPANY_FIELD):
		profile_company = frappe.db.get_value("User", user, USER_COMPANY_FIELD)
		if profile_company and frappe.db.exists("Company", profile_company):
			if _user_allowed_company(user, profile_company) and frappe.has_permission("Company", "read", doc=profile_company, user=user):
				return profile_company

	company = frappe.defaults.get_user_default("Company", user=user)
	if company and frappe.db.exists("Company", company):
		if _user_allowed_company(user, company) and frappe.has_permission("Company", "read", doc=company, user=user):
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
			if _user_allowed_company(user, permission.for_value) and frappe.has_permission("Company", "read", doc=permission.for_value, user=user):
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


def _companies_from_user_doc(doc):
	"""Read ordered companies from an unsaved User document without DB reads."""
	companies = [row.company for row in (doc.get(USER_ALLOWED_COMPANIES_FIELD) or []) if row.company]
	if doc.get(USER_COMPANY_FIELD) and doc.get(USER_COMPANY_FIELD) not in companies:
		companies.insert(0, doc.get(USER_COMPANY_FIELD))
	return list(dict.fromkeys(companies))


def prepare_user_company(doc, method=None):
	"""Validate and normalize the user's explicit POS company boundary."""
	if not is_multi_company_site() or doc.name in {"Administrator", "Guest"}:
		return
	if not frappe.db.has_column("User", USER_COMPANY_FIELD):
		return
	companies = _companies_from_user_doc(doc)
	if not companies:
		fallback = active_company()
		if fallback:
			companies = [fallback]
			doc.append(USER_ALLOWED_COMPANIES_FIELD, {"company": fallback})
	if not companies:
		frappe.throw(_("Select at least one allowed POS Company when creating a user in multiple-company mode."), frappe.ValidationError)
	for company in companies:
		if not frappe.db.exists("Company", company) or not frappe.has_permission("Company", "read", doc=company):
			frappe.throw(_("You cannot assign POS Company {0}.").format(company), frappe.PermissionError)
	# The selected/default company must always be in the allowed list.  The first
	# row is deliberately the default, making the setup predictable on login.
	doc.set(USER_COMPANY_FIELD, companies[0])


def sync_user_company_permission(doc, method=None):
	"""Synchronize native Company User Permissions with the User selector."""
	if not is_multi_company_site() or doc.name in {"Administrator", "Guest"}:
		return
	companies = _companies_from_user_doc(doc)
	if not companies:
		return
	existing = frappe.get_all(
		"User Permission", filters={"user": doc.name, "allow": "Company"}, fields=["name", "for_value"], limit_page_length=0
	)
	for permission in existing:
		if permission.for_value not in companies:
			# Company access is governed by the selector. Removing an old Company
			# permission prevents a stale manual grant from bypassing this boundary.
			frappe.delete_doc("User Permission", permission.name, ignore_permissions=True, force=True)
	for index, company in enumerate(companies):
		permission = next((row.name for row in existing if row.for_value == company), None)
		if permission:
			frappe.db.set_value("User Permission", permission, "is_default", int(index == 0), update_modified=False)
		else:
			frappe.get_doc(
				{
					"doctype": "User Permission",
					"user": doc.name,
					"allow": "Company",
					"for_value": company,
					"is_default": int(index == 0),
					"apply_to_all_doctypes": 1,
				}
			).insert(ignore_permissions=True)
	frappe.defaults.set_user_default("Company", companies[0], user=doc.name)
	frappe.clear_cache(user=doc.name)
