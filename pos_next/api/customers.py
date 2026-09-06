"""
POS Next Customer API
Handles customer search, creation, and management for POS operations
"""

import re

import frappe
from frappe import _

from pos_next.api.company_scope import OWNERSHIP_FIELD, assert_company_ownership, is_multi_company_site
from pos_next.api.feature_flags import resolve_pos_profile
from pos_next.api.party_contacts import require_mobile_no


SAUDI_ARABIA = "Saudi Arabia"
ARABIC_DIGIT_TRANSLATION = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
SAUDI_CITY_ALIASES = {
	"الريا ض": "الرياض",
	"الياض": "الرياض",
	"جده": "جدة",
	"مكه": "مكة المكرمة",
	"المدينه المنوره": "المدينة المنورة",
	"الاحساء": "الأحساء",
	"الضهران": "الظهران",
}
SAUDI_MAIN_CITIES = (
	"الرياض",
	"جدة",
	"مكة المكرمة",
	"المدينة المنورة",
	"الدمام",
	"الخبر",
	"الظهران",
	"الأحساء",
	"الطائف",
	"تبوك",
	"أبها",
	"خميس مشيط",
	"بريدة",
	"عنيزة",
	"حائل",
	"الجبيل",
	"ينبع",
	"نجران",
	"جازان",
	"سكاكا",
	"عرعر",
	"حفر الباطن",
	"الباحة",
)


def _resolve_customer_context(pos_profile=None, company=None):
	"""Resolve the POS company and country from an authorized profile."""
	if not pos_profile:
		return company, frappe.db.get_value("Company", company, "country") if company else None, None

	profile_name = resolve_pos_profile(pos_profile=pos_profile, company=company)
	profile = frappe.get_cached_doc("POS Profile", profile_name)
	company = profile.company
	country = frappe.db.get_value("Company", company, "country") or profile.get("country")
	return company, country, profile_name


def _normalize_tax_id(tax_id):
	return (tax_id or "").translate(ARABIC_DIGIT_TRANSLATION).strip()


def _validate_tax_id(company, tax_id, customer_type):
	"""Require a Saudi VAT number only for Saudi company customers."""
	tax_id = _normalize_tax_id(tax_id)
	if (
		frappe.db.get_value("Company", company, "country") == SAUDI_ARABIA
		and customer_type == "Company"
		and not re.fullmatch(r"\d{15}", tax_id)
	):
		frappe.throw(_("Saudi company customers require a 15-digit VAT number."))
	return tax_id


def _normalize_digits(value):
	return (value or "").translate(ARABIC_DIGIT_TRANSLATION).strip()


def _validate_customer_address(
	company,
	customer_type,
	address_line1=None,
	building_number=None,
	city=None,
	district=None,
	postal_code=None,
):
	"""Validate the standard Saudi national-address fields when required."""
	country = frappe.db.get_value("Company", company, "country")
	address = {
		"address_line1": (address_line1 or "").strip(),
		"building_number": _normalize_digits(building_number),
		"city": (city or "").strip(),
		"district": (district or "").strip(),
		"postal_code": _normalize_digits(postal_code),
		"country": country,
	}

	if country == SAUDI_ARABIA and customer_type == "Company":
		missing = [
			label
			for fieldname, label in (
				("address_line1", _("Street Address")),
				("building_number", _("Building Number")),
				("city", _("City")),
				("district", _("District")),
				("postal_code", _("Postal Code")),
			)
			if not address[fieldname]
		]
		if missing:
			frappe.throw(_("Please complete the Saudi national address: {0}").format(", ".join(missing)))

	if country == SAUDI_ARABIA:
		if address["building_number"] and not re.fullmatch(r"\d{4}", address["building_number"]):
			frappe.throw(_("Saudi Building Number must be exactly 4 digits."))
		if address["postal_code"] and not re.fullmatch(r"\d{5}", address["postal_code"]):
			frappe.throw(_("Saudi Postal Code must be exactly 5 digits."))

	return address


def _get_customer_address(customer):
	if not customer:
		return {}

	address_name = frappe.db.get_value("Customer", customer, "customer_primary_address")
	if not address_name:
		address_name = frappe.db.get_value(
			"Dynamic Link",
			{"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"},
			"parent",
		)
	if not address_name:
		return {}

	address = frappe.get_doc("Address", address_name)
	return {
		"address_line1": address.address_line1 or "",
		"building_number": address.get("custom_building_number") or address.get("building_no") or "",
		"city": address.city or "",
		"district": address.get("custom_area") or address.get("district") or address.state or "",
		"postal_code": address.pincode or "",
		"country": address.country or "",
	}


def _normalize_saudi_city(city):
	city = " ".join((city or "").split())
	return SAUDI_CITY_ALIASES.get(city, city)


def _get_saudi_address_options(country):
	"""Build reusable city and district suggestions from existing Saudi addresses."""
	if country != SAUDI_ARABIA:
		return {"cities": [], "districts_by_city": {}}

	address_meta = frappe.get_meta("Address")
	district_field = "custom_area" if address_meta.get_field("custom_area") else "state"
	rows = frappe.get_all(
		"Address",
		filters={"country": country},
		fields=["city", district_field],
		limit_page_length=0,
	)
	districts_by_city = {}
	for row in rows:
		city = _normalize_saudi_city(row.city)
		district = " ".join((row.get(district_field) or "").split())
		if not city or not district or district == "غير محدد":
			continue
		districts_by_city.setdefault(city, set()).add(district)

	cities = sorted(set(SAUDI_MAIN_CITIES) | set(districts_by_city))
	return {
		"cities": cities,
		"districts_by_city": {
			city: sorted(districts)
			for city, districts in districts_by_city.items()
		},
	}


def _upsert_customer_address(customer, address_data):
	if not any(address_data.get(key) for key in ("address_line1", "building_number", "city", "district", "postal_code")):
		return

	address_name = customer.customer_primary_address or frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Customer", "link_name": customer.name, "parenttype": "Address"},
		"parent",
	)
	address_values = {
		"address_title": customer.customer_name,
		"address_type": "Billing",
		"address_line1": address_data["address_line1"],
		"city": address_data["city"],
		"state": address_data["district"],
		"country": address_data["country"],
		"pincode": address_data["postal_code"],
		"is_primary_address": 1,
	}
	address_meta = frappe.get_meta("Address")
	for fieldname, value in (
		("building_no", address_data["building_number"]),
		("custom_building_number", address_data["building_number"]),
		("street_name", address_data["address_line1"]),
		("district", address_data["district"]),
		("custom_area", address_data["district"]),
	):
		if address_meta.get_field(fieldname):
			address_values[fieldname] = value

	if address_name and frappe.db.exists("Address", address_name):
		address = frappe.get_doc("Address", address_name)
		address.update(address_values)
		if not any(link.link_doctype == "Customer" and link.link_name == customer.name for link in address.links):
			address.append("links", {"link_doctype": "Customer", "link_name": customer.name})
		address.save(ignore_permissions=True)
	else:
		address = frappe.get_doc({"doctype": "Address", **address_values})
		address.append("links", {"link_doctype": "Customer", "link_name": customer.name})
		address.insert(ignore_permissions=True)

	customer.db_set("customer_primary_address", address.name, update_modified=False)


def _get_customer_form_extensions(pos_profile, company, customer=None):
	"""Load optional, app-provided POS customer form extensions."""
	extensions = []
	for handler_path in frappe.get_hooks("pos_next_customer_form_extensions"):
		extension = frappe.get_attr(handler_path)(pos_profile=pos_profile, company=company)
		if extension:
			extensions.append(extension)

	if customer:
		values = {}
		for handler_path in frappe.get_hooks("pos_next_customer_extension_values"):
			result = frappe.get_attr(handler_path)(
				customer=customer,
				pos_profile=pos_profile,
				company=company,
			)
			if result:
				values.update(result)
		for extension in extensions:
			extension["values"] = values.get(extension["id"], {})
	return extensions


def _get_payment_form_extensions(pos_profile, company, customer):
	"""Load optional fields contributed to the POS payment step by installed apps."""
	extensions = []
	for handler_path in frappe.get_hooks("pos_next_payment_form_extensions"):
		extension = frappe.get_attr(handler_path)(
			customer=customer,
			pos_profile=pos_profile,
			company=company,
		)
		if extension:
			extensions.append(extension)
	return extensions


def _run_customer_extensions(hook_name, customer, pos_profile, company, extension_data):
	"""Notify optional apps after a POS customer is safely saved."""
	data = frappe.parse_json(extension_data) if isinstance(extension_data, str) else extension_data or {}
	if not isinstance(data, dict):
		frappe.throw(_("Customer extension data must be an object."))
	for handler_path in frappe.get_hooks(hook_name):
		frappe.get_attr(handler_path)(
			customer=customer,
			pos_profile=pos_profile,
			company=company,
			extension_data=data,
		)


@frappe.whitelist()
def get_customer_form_context(pos_profile=None, customer=None):
	"""Return company-localized customer fields for the active POS profile."""
	company, country, resolved_profile = _resolve_customer_context(pos_profile=pos_profile)
	if customer:
		assert_company_ownership("Customer", customer)
	return {
		"company": company,
		"country": country,
		"is_saudi": country == SAUDI_ARABIA,
		"tax_address": _get_customer_address(customer),
		"address_options": _get_saudi_address_options(country),
		"extensions": _get_customer_form_extensions(resolved_profile, company, customer),
	}


@frappe.whitelist()
def get_payment_form_context(pos_profile, customer=None):
	"""Return customer summary and app-provided fields for the payment dialog."""
	company, country, resolved_profile = _resolve_customer_context(pos_profile=pos_profile)
	customer_name = customer.get("name") if isinstance(customer, dict) else customer
	if not customer_name:
		return {
			"company": company,
			"country": country,
			"customer": {},
			"extensions": [],
		}

	assert_company_ownership("Customer", customer_name)
	customer_values = frappe.db.get_value(
		"Customer",
		customer_name,
		["name", "customer_name", "mobile_no", "tax_id", "customer_type"],
		as_dict=True,
	) or {}
	customer_values["address"] = _get_customer_address(customer_name)
	return {
		"company": company,
		"country": country,
		"customer": customer_values,
		"extensions": _get_payment_form_extensions(
			resolved_profile,
			company,
			customer_name,
		),
	}


@frappe.whitelist()
def get_customers(search_term="", pos_profile=None, limit=20, modified_since=None):
	"""
	Search customers for inline customer selection in POS.

	Args:
	    search_term (str): Search query (name, mobile, or customer ID)
	    pos_profile (str): POS Profile to filter by customer group
	    limit (int): Maximum number of results to return
	    modified_since (str): Fetch customers modified after this timestamp (ISO format)

	Returns:
	    list: List of customer dictionaries with name, customer_name, mobile_no, email_id, disabled
	"""
	try:
		frappe.logger().debug(
			f"get_customers called with search_term={search_term}, pos_profile={pos_profile}, limit={limit}, modified_since={modified_since}"
		)

		filters = {}
		or_filters = []
		if is_multi_company_site() and not pos_profile:
			frappe.throw(_("A POS Profile is required in multiple-company mode."), frappe.PermissionError)

		# Filter by POS Profile customer group if specified
		if pos_profile:
			frappe.logger().debug(f"Loading POS Profile: {pos_profile}")
			pos_profile = resolve_pos_profile(pos_profile=pos_profile)
			profile_doc = frappe.get_cached_doc("POS Profile", pos_profile)
			if is_multi_company_site() and frappe.db.has_column("Customer", OWNERSHIP_FIELD):
				filters[OWNERSHIP_FIELD] = profile_doc.company
			# Check if customer_group field exists (it may not exist in all versions)
			if hasattr(profile_doc, "customer_group") and profile_doc.customer_group:
				filters["customer_group"] = profile_doc.customer_group
				frappe.logger().debug(f"Filtering by customer_group: {profile_doc.customer_group}")

		if modified_since:
			# Delta sync: include disabled customers so frontend can purge them
			filters["modified"] = [">=", modified_since]
		else:
			# Full fetch: only active customers
			filters["disabled"] = 0

		search_term = (search_term or "").strip()
		if search_term:
			like_term = f"%{search_term}%"
			or_filters = [
				["Customer", "name", "like", like_term],
				["Customer", "customer_name", "like", like_term],
				["Customer", "mobile_no", "like", like_term],
				["Customer", "email_id", "like", like_term],
			]

		customer_limit = limit if limit not in (None, 0) else frappe.db.count("Customer", filters)
		result = frappe.get_all(
			"Customer",
			filters=filters,
			or_filters=or_filters or None,
			fields=["name", "customer_name", "mobile_no", "email_id", "disabled"],
			limit=customer_limit,
			order_by="customer_name asc",
		)
		frappe.logger().debug(f"get_customers returned {len(result)} customers")
		return result
	except Exception as e:
		frappe.logger().error(f"Error in get_customers: {e!s}")
		frappe.logger().error(frappe.get_traceback())
		frappe.throw(_("Error fetching customers: {0}").format(str(e)))


@frappe.whitelist()
def create_customer(
	customer_name,
	mobile_no=None,
	email_id=None,
	customer_group=None,
	territory=None,
	company=None,
	pos_profile=None,
	custom_governorate=None,
	custom_district=None,
	tax_id=None,
	custom_commercial_registration=None,
	customer_type=None,
	tax_address_line1=None,
	tax_building_number=None,
	tax_city=None,
	tax_district=None,
	tax_postal_code=None,
	extension_data=None,
):
	"""
	Create a new customer from POS.

	Args:
	    customer_name (str): Customer name (required)
	    mobile_no (str): Mobile number (required)
	    email_id (str): Email address (optional, deprecated - kept for compatibility)
	    customer_group (str): Customer group (default: from Selling Settings)
	    territory (str): Territory (default: from Selling Settings)
	    company (str): Company (optional, used to auto-assign loyalty program)
	    pos_profile (str): POS Profile (optional, preferred for context-aware loyalty assignment)
	    custom_governorate (str): Governorate (optional)
	    custom_district (str): District (optional, must belong to the governorate)
	    tax_id (str): VAT / Tax registration number (optional)
	    custom_commercial_registration (str): Commercial Registration CR number (optional)
	    customer_type (str): Individual or Company (default: Individual)
	    tax_address_line1 (str): Street address for the Saudi national address

	Returns:
	    dict: Created customer document
	"""
	# Check if user has permission to create customers
	if not frappe.has_permission("Customer", "create"):
		frappe.throw(_("You don't have permission to create customers"), frappe.PermissionError)

	if not customer_name:
		frappe.throw(_("Customer name is required"))
	if is_multi_company_site() and not pos_profile:
		frappe.throw(_("A POS Profile is required in multiple-company mode."), frappe.PermissionError)

	company, _, pos_profile = _resolve_customer_context(pos_profile=pos_profile, company=company)
	require_mobile_no(mobile_no, "Customer")
	loyalty_program = get_default_loyalty_program_from_settings(company=company, pos_profile=pos_profile)

	resolved_customer_group = customer_group
	if not resolved_customer_group:
		resolved_customer_group = frappe.db.get_single_value("Selling Settings", "customer_group")
	if not resolved_customer_group:
		resolved_customer_group = (
			frappe.db.get_value("Customer Group", {"is_group": 0}, "name", order_by="lft")
			or "All Customer Groups"
		)

	resolved_territory = territory
	if not resolved_territory:
		resolved_territory = frappe.db.get_single_value("Selling Settings", "territory")
	if not resolved_territory:
		resolved_territory = (
			frappe.db.get_value("Territory", {"is_group": 0}, "name", order_by="lft") or "All Territories"
		)

	resolved_customer_type = customer_type if customer_type in ("Individual", "Company") else "Individual"
	tax_id = _validate_tax_id(company, tax_id, resolved_customer_type)
	address_data = _validate_customer_address(
		company,
		resolved_customer_type,
		tax_address_line1,
		tax_building_number,
		tax_city,
		tax_district,
		tax_postal_code,
	)

	customer_data = {
		"doctype": "Customer",
		"customer_name": customer_name,
		"customer_type": resolved_customer_type,
		"customer_group": resolved_customer_group,
		"territory": resolved_territory,
		"mobile_no": mobile_no or "",
		"custom_pos_mobile_no": mobile_no or "",
		"tax_id": tax_id,
		"loyalty_program": loyalty_program,
		"custom_governorate": custom_governorate or None,
		"custom_district": custom_district or None,
	}
	meta = frappe.get_meta("Customer")
	if meta.get_field("custom_vat_registration_number"):
		customer_data["custom_vat_registration_number"] = tax_id
	if meta.get_field("custom_commercial_registration"):
		customer_data["custom_commercial_registration"] = custom_commercial_registration or ""
	customer = frappe.get_doc(customer_data)
	if is_multi_company_site() and frappe.db.has_column("Customer", OWNERSHIP_FIELD):
		customer.set(OWNERSHIP_FIELD, company)

	frappe.flags.pos_next_customer_company = company
	frappe.flags.pos_next_customer_pos_profile = pos_profile
	try:
		# Permission is explicitly verified above, before any user supplied data is
		# used.  In a multi-company site Frappe performs a second document-level
		# create check on a new Customer before its company ownership hook runs;
		# that check has no owner value yet and incorrectly rejects an authorized
		# cashier.  The POS endpoint has already resolved and authorized the active
		# profile/company, so skip only this duplicate check.
		customer.insert(ignore_permissions=True)
		_upsert_customer_address(customer, address_data)
	finally:
		frappe.flags.pos_next_customer_company = None
		frappe.flags.pos_next_customer_pos_profile = None

	_run_customer_extensions("pos_next_customer_created", customer, pos_profile, company, extension_data)
	return customer.as_dict()


@frappe.whitelist()
def update_customer(
	name,
	customer_name,
	mobile_no=None,
	customer_group=None,
	territory=None,
	company=None,
	pos_profile=None,
	custom_governorate=None,
	custom_district=None,
	tax_id=None,
	custom_commercial_registration=None,
	customer_type=None,
	tax_address_line1=None,
	tax_building_number=None,
	tax_city=None,
	tax_district=None,
	tax_postal_code=None,
	extension_data=None,
):
	"""Update a POS customer and its country-aware address and extensions."""
	if not name or not frappe.db.exists("Customer", name):
		frappe.throw(_("Customer is required"))
	if not customer_name:
		frappe.throw(_("Customer name is required"))

	company, _, pos_profile = _resolve_customer_context(pos_profile=pos_profile, company=company)
	assert_company_ownership("Customer", name)
	customer = frappe.get_doc("Customer", name)
	if not frappe.has_permission("Customer", "write", doc=customer):
		frappe.throw(_("You don't have permission to update customers"), frappe.PermissionError)

	require_mobile_no(mobile_no, "Customer")
	resolved_customer_type = customer_type if customer_type in ("Individual", "Company") else "Individual"
	tax_id = _validate_tax_id(company, tax_id, resolved_customer_type)
	address_data = _validate_customer_address(
		company,
		resolved_customer_type,
		tax_address_line1,
		tax_building_number,
		tax_city,
		tax_district,
		tax_postal_code,
	)

	values = {
		"customer_name": customer_name,
		"customer_type": resolved_customer_type,
		"customer_group": customer_group or customer.customer_group,
		"territory": territory or customer.territory,
		"mobile_no": mobile_no or "",
		"custom_pos_mobile_no": mobile_no or "",
		"tax_id": tax_id,
		"custom_governorate": custom_governorate or None,
		"custom_district": custom_district or None,
	}
	meta = frappe.get_meta("Customer")
	if meta.get_field("custom_vat_registration_number"):
		values["custom_vat_registration_number"] = tax_id
	if meta.get_field("custom_commercial_registration"):
		values["custom_commercial_registration"] = custom_commercial_registration or ""

	customer.update(values)
	customer.save(ignore_permissions=True)
	_upsert_customer_address(customer, address_data)
	_run_customer_extensions("pos_next_customer_updated", customer, pos_profile, company, extension_data)
	return customer.as_dict()


def get_default_loyalty_program(company):
	"""
	Get the default loyalty program for a company.
	Prefers programs with auto_opt_in enabled.

	Args:
	    company (str): Company name

	Returns:
	    str: Loyalty program name or None
	"""
	# First try to find a loyalty program with auto_opt_in for the company
	loyalty_program = frappe.db.get_value("Loyalty Program", {"company": company, "auto_opt_in": 1}, "name")

	if loyalty_program:
		return loyalty_program

	# Fallback: any loyalty program for the company
	loyalty_program = frappe.db.get_value("Loyalty Program", {"company": company}, "name")

	return loyalty_program


def auto_assign_loyalty_program(doc, method=None):
	"""
	Auto-assign loyalty program to newly created customers.
	Called as after_insert hook on Customer doctype.

	Uses the default_loyalty_program from POS Settings.
	If no loyalty program is configured in POS Settings, no auto-assignment occurs.

	Args:
	    doc: Customer document
	    method: Hook method name (not used)
	"""
	# Skip if customer already has a loyalty program
	if doc.loyalty_program:
		return

	company, pos_profile = _get_customer_assignment_context()
	loyalty_program = get_default_loyalty_program_from_settings(
		company=company,
		pos_profile=pos_profile,
	)

	if loyalty_program:
		# Use db_set to avoid triggering validate hooks again
		doc.db_set("loyalty_program", loyalty_program, update_modified=False)
		frappe.logger().info(f"Auto-assigned loyalty program '{loyalty_program}' to customer '{doc.name}'")


def _get_customer_assignment_context():
	"""Get company/profile context for customer auto-assignment from the current request."""
	company = getattr(frappe.flags, "pos_next_customer_company", None)
	pos_profile = getattr(frappe.flags, "pos_next_customer_pos_profile", None)

	form_dict = getattr(frappe.local, "form_dict", None)
	if form_dict:
		company = company or form_dict.get("company")
		pos_profile = pos_profile or form_dict.get("pos_profile")

	return company, pos_profile


def get_default_loyalty_program_from_settings(company=None, pos_profile=None):
	"""
	Get the default loyalty program from POS Settings using explicit context.
	Returns a program only when the company/profile context is clear enough to avoid
	assigning the wrong loyalty program.

	Returns:
	    str: Loyalty program name or None if not configured
	"""
	if pos_profile:
		pos_settings = frappe.db.get_value(
			"POS Settings",
			{"enabled": 1, "pos_profile": pos_profile},
			"default_loyalty_program",
		)
		return pos_settings or None

	if not company:
		return None

	pos_settings = frappe.get_all(
		"POS Settings",
		filters={"enabled": 1, "default_loyalty_program": ["is", "set"]},
		fields=["pos_profile", "default_loyalty_program"],
		order_by="modified desc",
	)

	company_programs = []
	for row in pos_settings:
		profile_company = frappe.get_cached_value("POS Profile", row.pos_profile, "company")
		if profile_company == company:
			company_programs.append(row.default_loyalty_program)

	unique_programs = list(dict.fromkeys(program for program in company_programs if program))
	if len(unique_programs) == 1:
		return unique_programs[0]

	return None


@frappe.whitelist()
def get_customer_details(customer):
	"""
	Get detailed customer information.

	Args:
	    customer (str): Customer ID

	Returns:
	    dict: Customer details
	"""
	if not customer:
		frappe.throw(_("Customer is required"))

	assert_company_ownership("Customer", customer)
	return frappe.get_cached_doc("Customer", customer).as_dict()
