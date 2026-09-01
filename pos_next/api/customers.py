"""
POS Next Customer API
Handles customer search, creation, and management for POS operations
"""

import frappe
from frappe import _


def _validate_tax_id(tax_id):
	tax_id = (tax_id or "").strip()
	if tax_id and (not tax_id.isdigit() or len(tax_id) != 15):
		frappe.throw(_("Tax ID must be exactly 15 digits"))
	return tax_id


def _validate_tax_address(vat_registration_number, address_line1, building_number, city, district, postal_code):
	vat_registration_number = _validate_tax_id(vat_registration_number)
	address_line1 = (address_line1 or "").strip()
	building_number = (building_number or "").strip()
	city = (city or "").strip()
	district = (district or "").strip()
	postal_code = (postal_code or "").strip()

	if vat_registration_number:
		missing = []
		if not address_line1:
			missing.append(_("Tax Address"))
		if not building_number:
			missing.append(_("Building Number"))
		if not city:
			missing.append(_("City"))
		if not district:
			missing.append(_("District"))
		if not postal_code:
			missing.append(_("Postal Code"))
		if missing:
			frappe.throw(_("Please complete tax address fields: {0}").format(", ".join(missing)))

	if building_number and (not building_number.isdigit() or len(building_number) != 4):
		frappe.throw(_("Building Number must be exactly 4 digits"))
	if postal_code and (not postal_code.isdigit() or len(postal_code) != 5):
		frappe.throw(_("Postal Code must be exactly 5 digits"))

	return {
		"vat_registration_number": vat_registration_number,
		"address_line1": address_line1,
		"building_number": building_number,
		"city": city,
		"district": district,
		"postal_code": postal_code,
	}


def _get_customer_tax_address(customer_name):
	if not customer_name:
		return {}

	address_name = frappe.db.get_value("Customer", customer_name, "customer_primary_address")
	if not address_name:
		address_name = frappe.db.get_value(
			"Dynamic Link",
			{"link_doctype": "Customer", "link_name": customer_name, "parenttype": "Address"},
			"parent",
		)
	if not address_name:
		return {}

	address = frappe.db.get_value(
		"Address",
		address_name,
		[
			"address_line1",
			"building_no",
			"custom_building_number",
			"city",
			"district",
			"custom_area",
			"pincode",
		],
		as_dict=True,
	)
	if not address:
		return {}

	return {
		"tax_address_line1": address.address_line1 or "",
		"tax_building_number": address.custom_building_number or address.building_no or "",
		"tax_city": address.city or "",
		"tax_district": address.custom_area or address.district or "",
		"tax_postal_code": address.pincode or "",
	}


def _upsert_customer_tax_address(customer, address_data):
	has_address = any(
		address_data.get(key)
		for key in ["address_line1", "building_number", "city", "district", "postal_code"]
	)
	if not has_address:
		return

	address_name = customer.customer_primary_address
	if not address_name:
		address_name = frappe.db.get_value(
			"Dynamic Link",
			{"link_doctype": "Customer", "link_name": customer.name, "parenttype": "Address"},
			"parent",
		)

	address_values = {
		"address_title": customer.customer_name,
		"address_type": "Billing",
		"address_line1": address_data["address_line1"],
		"city": address_data["city"],
		"country": "Saudi Arabia",
		"pincode": address_data["postal_code"],
		"is_primary_address": 1,
		"building_no": address_data["building_number"],
		"custom_building_number": address_data["building_number"],
		"street_name": address_data["address_line1"],
		"district": address_data["district"],
		"custom_area": address_data["district"],
	}

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
	    list: List of customer dictionaries with name, customer_name, mobile_no, email_id, vehicle fields, disabled
	"""
	try:
		frappe.logger().debug(
			f"get_customers called with search_term={search_term}, pos_profile={pos_profile}, limit={limit}, modified_since={modified_since}"
		)

		filters = {}
		or_filters = []

		# Filter by POS Profile customer group if specified
		if pos_profile:
			frappe.logger().debug(f"Loading POS Profile: {pos_profile}")
			profile_doc = frappe.get_cached_doc("POS Profile", pos_profile)
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
				["Customer", "tax_id", "like", like_term],
				["Customer", "custom_vat_registration_number", "like", like_term],
				["Customer", "email_id", "like", like_term],
				["Customer", "moh_vehicle_plate_number", "like", like_term],
			]

		customer_limit = limit if limit not in (None, 0) else frappe.db.count("Customer", filters)
		result = frappe.get_all(
			"Customer",
			filters=filters,
			or_filters=or_filters or None,
			fields=[
				"name",
				"customer_name",
				"mobile_no",
				"tax_id",
				"custom_vat_registration_number",
				"email_id",
				"customer_group",
				"territory",
				"custom_governorate",
				"custom_district",
				"moh_vehicle_type",
				"moh_vehicle_plate_number",
				"moh_vehicle_chassis_number",
				"disabled",
			],
			limit=customer_limit,
			order_by="customer_name asc",
		)
		for customer in result:
			customer.update(_get_customer_tax_address(customer.name))
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
	tax_id=None,
	custom_vat_registration_number=None,
	tax_address_line1=None,
	tax_building_number=None,
	tax_city=None,
	tax_district=None,
	tax_postal_code=None,
	email_id=None,
	customer_group=None,
	territory=None,
	company=None,
	pos_profile=None,
	custom_governorate=None,
	custom_district=None,
	moh_vehicle_type=None,
	moh_vehicle_plate_number=None,
	moh_vehicle_chassis_number=None,
):
	"""
	Create a new customer from POS.

	Args:
	    customer_name (str): Customer name (required)
	    mobile_no (str): Mobile number (optional)
	    custom_vat_registration_number (str): VAT registration number for ZATCA
	    email_id (str): Email address (optional)
	    customer_group (str): Customer group (default: from Selling Settings)
	    territory (str): Territory (default: from Selling Settings)
	    company (str): Company (optional, used to auto-assign loyalty program)
	    pos_profile (str): POS Profile (optional, preferred for context-aware loyalty assignment)
	    custom_governorate (str): Governorate (optional)
	    custom_district (str): District (optional, must belong to the governorate)
	    moh_vehicle_type (str): Customer vehicle type (optional)
	    moh_vehicle_plate_number (str): Customer vehicle plate number (optional)
	    moh_vehicle_chassis_number (str): Customer vehicle chassis number (optional)

	Returns:
	    dict: Created customer document
	"""
	# Check if user has permission to create customers
	if not frappe.has_permission("Customer", "create"):
		frappe.throw(_("You don't have permission to create customers"), frappe.PermissionError)

	if not customer_name:
		frappe.throw(_("Customer name is required"))
	address_data = _validate_tax_address(
		custom_vat_registration_number or tax_id,
		tax_address_line1,
		tax_building_number,
		tax_city,
		tax_district,
		tax_postal_code,
	)
	vat_registration_number = address_data["vat_registration_number"]

	loyalty_program = get_default_loyalty_program_from_settings(
		company=company,
		pos_profile=pos_profile,
	)

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

	customer = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": customer_name,
			"customer_type": "Individual",
			"customer_group": resolved_customer_group,
			"territory": resolved_territory,
			"mobile_no": mobile_no or "",
			"tax_id": vat_registration_number,
			"custom_vat_registration_number": vat_registration_number,
			"tax_category": "Standard Tax Customer" if vat_registration_number else None,
			"email_id": email_id or "",
			"loyalty_program": loyalty_program,
			"custom_governorate": custom_governorate or None,
			"custom_district": custom_district or None,
			"moh_vehicle_type": moh_vehicle_type or "",
			"moh_vehicle_plate_number": moh_vehicle_plate_number or "",
			"moh_vehicle_chassis_number": moh_vehicle_chassis_number or "",
		}
	)

	frappe.flags.pos_next_customer_company = company
	frappe.flags.pos_next_customer_pos_profile = pos_profile
	try:
		customer.insert()
		_upsert_customer_tax_address(customer, address_data)
	finally:
		frappe.flags.pos_next_customer_company = None
		frappe.flags.pos_next_customer_pos_profile = None

	return customer.as_dict()


@frappe.whitelist()
def update_customer(
	name,
	customer_name,
	mobile_no=None,
	tax_id=None,
	custom_vat_registration_number=None,
	tax_address_line1=None,
	tax_building_number=None,
	tax_city=None,
	tax_district=None,
	tax_postal_code=None,
	email_id=None,
	customer_group=None,
	territory=None,
	custom_governorate=None,
	custom_district=None,
	moh_vehicle_type=None,
	moh_vehicle_plate_number=None,
	moh_vehicle_chassis_number=None,
):
	if not frappe.has_permission("Customer", "write"):
		frappe.throw(_("You don't have permission to update customers"), frappe.PermissionError)
	if not name or not frappe.db.exists("Customer", name):
		frappe.throw(_("Customer is required"))
	if not customer_name:
		frappe.throw(_("Customer name is required"))

	customer = frappe.get_doc("Customer", name)
	address_data = _validate_tax_address(
		custom_vat_registration_number or tax_id,
		tax_address_line1,
		tax_building_number,
		tax_city,
		tax_district,
		tax_postal_code,
	)
	vat_registration_number = address_data["vat_registration_number"]
	customer.update(
		{
			"customer_name": customer_name,
			"customer_group": customer_group or customer.customer_group,
			"territory": territory or customer.territory,
			"mobile_no": mobile_no or "",
			"tax_id": vat_registration_number,
			"custom_vat_registration_number": vat_registration_number,
			"tax_category": "Standard Tax Customer" if vat_registration_number else None,
			"email_id": email_id or "",
			"custom_governorate": custom_governorate or None,
			"custom_district": custom_district or None,
			"moh_vehicle_type": moh_vehicle_type or "",
			"moh_vehicle_plate_number": moh_vehicle_plate_number or "",
			"moh_vehicle_chassis_number": moh_vehicle_chassis_number or "",
		}
	)
	customer.save()
	_upsert_customer_tax_address(customer, address_data)
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

	return frappe.get_cached_doc("Customer", customer).as_dict()
