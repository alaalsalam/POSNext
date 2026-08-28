"""Idempotent defaults for a ready-to-sell POS Profile."""

from contextlib import contextmanager

import frappe

from pos_next.api.company_scope import OWNERSHIP_FIELD, is_multi_company_site


@contextmanager
def _company_setup_context(company):
	"""Allow trusted setup code to create company-owned master records."""
	previous = getattr(frappe.flags, "pos_next_setup_company", None)
	frappe.flags.pos_next_setup_company = company
	try:
		yield
	finally:
		frappe.flags.pos_next_setup_company = previous


def _company_group(doctype, fieldname, parent_fieldname, label, company, parent):
	"""Return a leaf group owned by the company, creating it when needed."""
	group_name = f"{label} · {company}"[:140]
	if frappe.db.exists(doctype, group_name):
		if is_multi_company_site() and frappe.db.has_column(doctype, OWNERSHIP_FIELD):
			owner = frappe.db.get_value(doctype, group_name, OWNERSHIP_FIELD)
			if owner and owner != company:
				frappe.throw(
					f"{doctype} {group_name} is already owned by {owner}; it cannot be reused for {company}."
				)
			frappe.db.set_value(
				doctype,
				group_name,
				{fieldname: group_name, parent_fieldname: parent, "is_group": 0, OWNERSHIP_FIELD: company},
				update_modified=False,
			)
		return group_name

	doc = frappe.get_doc(
		{
			"doctype": doctype,
			fieldname: group_name,
			parent_fieldname: parent,
			"is_group": 0,
		}
	)
	if is_multi_company_site() and frappe.db.has_column(doctype, OWNERSHIP_FIELD):
		doc.set(OWNERSHIP_FIELD, company)
	with _company_setup_context(company):
		doc.insert(ignore_permissions=True)
	return doc.name


def _root_group(doctype, parent_fieldname):
	"""Find the localized ERPNext root group instead of assuming its English name."""
	root = frappe.get_all(
		doctype,
		filters={"is_group": 1, parent_fieldname: ["in", ["", None]]},
		pluck="name",
		limit_page_length=1,
	)
	if not root:
		frappe.throw(f"A root {doctype} is required before creating POS defaults.")
	return root[0]


def _first_leaf(doctype):
	leaf = frappe.get_all(doctype, filters={"is_group": 0}, pluck="name", limit_page_length=1)
	if not leaf:
		frappe.throw(f"A leaf {doctype} is required before creating POS defaults.")
	return leaf[0]


def _default_customer_for_company(company, customer_group):
	"""Create the system walk-in customer once per company.

	It is intentionally not a real contact, so it is exempt from the POS mobile
	requirement used for customers that operators create.
	"""
	customer_name = f"عميل نقدي · {company}"[:140]
	if not frappe.db.exists("Customer", customer_name):
		customer = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": customer_name,
				"customer_type": "Individual",
				"customer_group": customer_group,
				"territory": _first_leaf("Territory"),
			}
		)
		if is_multi_company_site() and frappe.db.has_column("Customer", OWNERSHIP_FIELD):
			customer.set(OWNERSHIP_FIELD, company)
		with _company_setup_context(company):
			customer.insert(ignore_permissions=True, ignore_mandatory=True)
	else:
		updates = {"customer_group": customer_group}
		if is_multi_company_site() and frappe.db.has_column("Customer", OWNERSHIP_FIELD):
			updates[OWNERSHIP_FIELD] = company
		frappe.db.set_value("Customer", customer_name, updates, update_modified=False)
	return customer_name


def _default_supplier_for_company(company, supplier_group):
	"""Create one clearly-labelled system supplier per company.

	A new POS profile needs a usable purchase draft immediately. This is a system
	default, not a supplier contact, so no invented phone number is stored. Real
	suppliers created from POS still require a mobile number.
	"""
	supplier_name = f"مورد افتراضي · {company}"[:140]
	if not frappe.db.exists("Supplier", supplier_name):
		supplier = frappe.get_doc(
			{
				"doctype": "Supplier",
				"supplier_name": supplier_name,
				"supplier_group": supplier_group,
				"supplier_type": "Company",
			}
		)
		if is_multi_company_site() and frappe.db.has_column("Supplier", OWNERSHIP_FIELD):
			supplier.set(OWNERSHIP_FIELD, company)
		with _company_setup_context(company):
			supplier.insert(ignore_permissions=True, ignore_mandatory=True)
	else:
		updates = {"supplier_group": supplier_group}
		if is_multi_company_site() and frappe.db.has_column("Supplier", OWNERSHIP_FIELD):
			updates[OWNERSHIP_FIELD] = company
		frappe.db.set_value("Supplier", supplier_name, updates, update_modified=False)
	return supplier_name


def provision_company_pos_defaults(company):
	"""Provision isolated POS masters for one company, idempotently."""
	if not company or not frappe.db.exists("Company", company):
		return {}
	item_group = _company_group(
		"Item Group", "item_group_name", "parent_item_group", "أصناف نقطة البيع", company,
		_root_group("Item Group", "parent_item_group"),
	)
	customer_group = _company_group(
		"Customer Group", "customer_group_name", "parent_customer_group", "عملاء نقطة البيع", company,
		_root_group("Customer Group", "parent_customer_group"),
	)
	supplier_group = _company_group(
		"Supplier Group", "supplier_group_name", "parent_supplier_group", "موردو نقطة البيع", company,
		_root_group("Supplier Group", "parent_supplier_group"),
	)
	return {
		"item_group": item_group,
		"customer_group": customer_group,
		"supplier_group": supplier_group,
		"default_customer": _default_customer_for_company(company, customer_group),
		"default_supplier": _default_supplier_for_company(company, supplier_group),
	}


def ensure_company_pos_defaults(doc, method=None):
	"""Company hook: always prepare POS master data for a new company.

	Ownership becomes mandatory as soon as the tenant enables Multiple Companies;
	provisioning early also makes a freshly installed site immediately ready.
	"""
	provision_company_pos_defaults(getattr(doc, "name", doc))


def provision_all_company_pos_defaults():
	"""Repair/provision every company after multi-company mode is enabled."""
	result = {}
	for company in frappe.get_all("Company", pluck="name", limit_page_length=0):
		result[company] = provision_company_pos_defaults(company)
	return result


def normalize_company_pos_masters(protected_companies=("spare parts",)):
	"""Put company-owned POS masters into their canonical isolated groups.

	Unowned legacy records are intentionally not guessed or reassigned.  In a
	multi-company site they remain fail-closed until an administrator explicitly
	chooses their owner, protecting the preserved company from accidental moves.
	"""
	protected = set(protected_companies or [])
	report = {"companies": {}, "protected_companies": sorted(protected)}
	for company in frappe.get_all("Company", pluck="name", limit_page_length=0):
		if company in protected:
			continue
		defaults = provision_company_pos_defaults(company)
		counts = {}
		for doctype, group_field, group_name in (
			("Customer", "customer_group", defaults["customer_group"]),
			("Supplier", "supplier_group", defaults["supplier_group"]),
			("Item", "item_group", defaults["item_group"]),
		):
			if not frappe.db.has_column(doctype, OWNERSHIP_FIELD):
				continue
			filters = {OWNERSHIP_FIELD: company, group_field: ["!=", group_name]}
			counts[doctype] = frappe.db.count(doctype, filters)
			if counts[doctype]:
				frappe.db.set_value(doctype, filters, group_field, group_name, update_modified=False)
		report["companies"][company] = counts
	frappe.clear_cache()
	return report


def classify_company_items(protected_companies=("spare parts",)):
	"""Replace legacy item-group clutter with a small, company-owned taxonomy."""
	protected = set(protected_companies or [])
	taxonomy = {
		"Phones": [("هواتف ذكية", ("iphone", "samsung", "honor", "huawei", "infinix", "redmi", "phone", "جوال")), ("أجهزة لوحية", ("ipad", "tablet", "tab")), ("سماعات", ("airpod", "headphone", "سماعة")), ("شواحن وكابلات", ("charger", "power", "usb", "lightning", "شاحن", "كيبل")), ("حماية وإكسسوارات", ("case", "glass", "cover", "جراب", "كفر", "حماية")), ("ملحقات إلكترونية", ())],
		"Flowers": [("نباتات وأشجار", ("شجر", "نبات", "خزام", "اجلونيما", "اتل")), ("تنسيقات وورود", ("ورد", "valentine", "love", "bouquet")), ("أحواض ومستلزمات", ("حوض", "ابزور", "تربة")), ("هدايا وتنسيقات", ())],
		"Cafe": [("مشروبات ساخنة", ("قهوة", "coffee", "hot")), ("مشروبات باردة", ("بارد", "mojito", "عصير")), ("حلويات ومخبوزات", ("حلا", "كرواس", "cake")), ("منتجات المقهى", ())],
		"Super Market": [("مياه ومشروبات", ("ماء", "مياه", "juice", "عصير", "مشروب")), ("معلبات وبقالة", ("معلب", "rice", "رز", "سكر", "دقيق")), ("وجبات خفيفة وحلويات", ("snack", "dissert", "شوكولا", "بسكويت")), ("منتجات السوبرماركت", ())],
	}
	default_categories = {
		"Pharmacy": "منتجات الصيدلية", "Gold and Jewelry": "ذهب ومجوهرات", "Restaurant": "منتجات المطعم",
		"Glasses": "نظارات وملحقاتها", "Electrical Appliances": "أجهزة وملحقات", "Perfumes": "عطور وملحقات",
		"Chocolates": "شوكولاتة وحلويات", "Toys": "ألعاب ومنتجات الأطفال", "Hairdressing": "العناية والجمال",
		"Ice Cream": "آيس كريم ومشروبات", "Pizza": "بيتزا ومنتجات المطعم", "Commercial": "منتجات تجارية", "Cafe": "منتجات المقهى",
	}
	report = {}
	for company in frappe.get_all("Company", pluck="name", limit_page_length=0):
		if company in protected:
			continue
		root = provision_company_pos_defaults(company)["item_group"]
		# Move existing items out first, then promote the company root to a folder.
		frappe.db.set_value("Item", {OWNERSHIP_FIELD: company, "item_group": root}, "item_group", None, update_modified=False)
		frappe.db.set_value("Item Group", root, "is_group", 1, update_modified=False)
		categories = taxonomy.get(company, [(default_categories.get(company, f"منتجات {company}"), ())])
		created = {}
		for label, _keywords in categories:
			name = f"{label} · {company}"[:140]
			if not frappe.db.exists("Item Group", name):
				with _company_setup_context(company):
					frappe.get_doc({"doctype": "Item Group", "item_group_name": name, "parent_item_group": root, "is_group": 0, OWNERSHIP_FIELD: company}).insert(ignore_permissions=True)
			created[label] = name
		counts = {label: 0 for label in created}
		for item in frappe.get_all("Item", filters={OWNERSHIP_FIELD: company}, fields=["name", "item_name", "item_code"], limit_page_length=0):
			text = f"{item.item_name or ''} {item.item_code or ''}".lower()
			label = next((label for label, words in categories if words and any(word.lower() in text for word in words)), categories[-1][0])
			frappe.db.set_value("Item", item.name, "item_group", created[label], update_modified=False)
			counts[label] += 1
		report[company] = counts
	frappe.clear_cache()
	return report


def repair_user_company_boundaries():
	"""Migrate existing users to the explicit allowed-company selector safely.

	Existing Company User Permissions are adopted on the first run so upgrading a
	site never silently removes a user's current company access. Later saves use
	the User selector as the single source of truth and remove stale grants.
	"""
	from pos_next.api.company_scope import (
		USER_ALLOWED_COMPANIES_FIELD,
		USER_COMPANY_FIELD,
	)

	if not is_multi_company_site() or not frappe.get_meta("User").has_field(USER_ALLOWED_COMPANIES_FIELD):
		return 0
	updated = 0
	for user_name in frappe.get_all("User", filters={"name": ["not in", ["Administrator", "Guest"]]}, pluck="name", limit_page_length=0):
		user = frappe.get_doc("User", user_name)
		current = [row.company for row in (user.get(USER_ALLOWED_COMPANIES_FIELD) or []) if row.company]
		if not current:
			default = user.get(USER_COMPANY_FIELD)
			permissions = frappe.get_all(
				"User Permission",
				filters={"user": user.name, "allow": "Company"},
				fields=["for_value", "is_default"],
				order_by="is_default desc, creation asc",
				limit_page_length=0,
			)
			companies = ([default] if default else []) + [row.for_value for row in permissions]
			for company in dict.fromkeys(company for company in companies if company and frappe.db.exists("Company", company)):
				user.append(USER_ALLOWED_COMPANIES_FIELD, {"company": company})
			current = [row.company for row in user.get(USER_ALLOWED_COMPANIES_FIELD)]
		if current:
			user.set(USER_COMPANY_FIELD, current[0])
			# Saving persists the child-table rows and the User hook synchronizes the
			# native Company User Permissions in the same transaction.
			user.save(ignore_permissions=True)
			updated += 1
	return updated


def sync_multi_company_defaults(doc=None, method=None):
	"""Provision all company branches when an administrator enables the mode."""
	if not is_multi_company_site():
		return
	provision_all_company_pos_defaults()
	for name in frappe.get_all("POS Profile", filters={"disabled": 0}, pluck="name", limit_page_length=0):
		ensure_pos_profile_defaults(frappe.get_doc("POS Profile", name))
	repair_user_company_boundaries()
	frappe.clear_cache()


def _default_customer(profile):
	company = profile.company
	defaults = provision_company_pos_defaults(company)
	# Keep an explicitly selected real customer in single-company mode. In
	# multi-company mode it must belong to the active company, otherwise use the
	# company's walk-in customer so cross-company data cannot leak into the POS.
	customer_name = profile.customer if profile.customer and frappe.db.exists("Customer", profile.customer) else None
	if is_multi_company_site() and customer_name:
		owner = frappe.db.get_value("Customer", customer_name, OWNERSHIP_FIELD)
		if owner != company:
			customer_name = None
	profile.customer = customer_name or defaults["default_customer"]
	return profile.customer


def _default_item_group(profile):
	group = provision_company_pos_defaults(profile.company)["item_group"]
	if profile.get("item_groups"):
		if not is_multi_company_site():
			return None
		if any(
			frappe.db.get_value("Item Group", row.item_group, OWNERSHIP_FIELD) == profile.company
			for row in profile.item_groups
		):
			return None
	profile.append("item_groups", {"item_group": group})
	return group


def _set_profile_default_supplier(profile, supplier):
	"""Fill an empty per-profile purchase default without overwriting a choice."""
	settings_name = frappe.db.get_value("POS Settings", {"pos_profile": profile.name}, "name")
	if settings_name and not frappe.db.get_value("POS Settings", settings_name, "posa_default_supplier"):
		frappe.db.set_value(
			"POS Settings", settings_name, "posa_default_supplier", supplier, update_modified=False
		)


def ensure_pos_profile_defaults(doc, method=None):
	"""Make a new POS Profile usable without manual master-data setup.

	An explicitly selected customer or item-group configuration is always kept.
	Only missing pieces receive company-owned defaults.
	"""
	profile = doc if getattr(doc, "doctype", None) == "POS Profile" else frappe.get_doc("POS Profile", doc)
	if not profile.company:
		return

	company_defaults = provision_company_pos_defaults(profile.company)
	default_customer = _default_customer(profile)
	default_group = _default_item_group(profile)
	_set_profile_default_supplier(profile, company_defaults["default_supplier"])
	if default_group:
		# A newly created profile has no legacy child links, so saving its one
		# default group is safe.  Existing demo profiles may contain historical
		# links that need separate repair and must not block a default customer.
		profile.save(ignore_permissions=True)
	else:
		frappe.db.set_value("POS Profile", profile.name, "customer", default_customer, update_modified=False)
	_invalidate_profile_cache(profile.name)


def _clone_shared_demo_item_groups(profiles):
	"""Split legacy shared demo groups so each company owns its catalog branch."""
	by_group = {}
	for profile in profiles:
		for row in profile.get("item_groups", []):
			by_group.setdefault(row.item_group, []).append(profile)

	cloned = []
	for source_group, owners in by_group.items():
		companies = {profile.company for profile in owners}
		if len(companies) < 2 or not frappe.db.exists("Item Group", source_group):
			continue
		# The demo's shared groups are saleable leaf groups.  Do not attempt to
		# silently clone an arbitrary hierarchy in a real tenant.
		if frappe.db.get_value("Item Group", source_group, "is_group"):
			continue
		for profile in owners:
			clone = f"{source_group} · {profile.company}"[:140]
			if not frappe.db.exists("Item Group", clone):
				group = frappe.get_doc(
					{
						"doctype": "Item Group",
						"item_group_name": clone,
						"parent_item_group": _root_group("Item Group", "parent_item_group"),
						"is_group": 0,
						OWNERSHIP_FIELD: profile.company,
					}
				)
				with _company_setup_context(profile.company):
					group.insert(ignore_permissions=True)
			frappe.db.set_value(
				"Item", {"item_group": source_group, OWNERSHIP_FIELD: profile.company}, "item_group", clone, update_modified=False
			)
			frappe.db.set_value(
				"POS Item Group", {"parent": profile.name, "item_group": source_group}, "item_group", clone, update_modified=False
			)
			cloned.append(clone)
	return cloned


def _remove_stale_profile_group_links():
	"""Remove only child rows whose referenced Item Group no longer exists."""
	stale = [
		row.name
		for row in frappe.get_all("POS Item Group", fields=["name", "item_group"], limit_page_length=0)
		if not frappe.db.exists("Item Group", row.item_group)
	]
	for name in stale:
		frappe.db.delete("POS Item Group", {"name": name})
	return stale


def prepare_demo_pos_defaults():
	"""Bring every existing demo profile to the same ready-to-sell baseline."""
	stale_group_links = _remove_stale_profile_group_links()
	profiles = [
		frappe.get_doc("POS Profile", name)
		for name in frappe.get_all("POS Profile", filters={"disabled": 0}, pluck="name")
	]
	customers = []
	for profile in profiles:
		before = profile.customer
		ensure_pos_profile_defaults(profile)
		if not before:
			customers.append(profile.customer)
		# Reload because the save in the setup function may have added defaults.
		profile.reload()
	cloned_groups = _clone_shared_demo_item_groups(profiles)
	for profile in profiles:
		_invalidate_profile_cache(profile.name)
	frappe.clear_cache()
	return {
		"profiles": len(profiles),
		"default_customers": customers,
		"split_item_groups": cloned_groups,
		"removed_stale_group_links": len(stale_group_links),
	}


def _invalidate_profile_cache(profile):
	cache = frappe.cache()
	cache.delete_value(f"pos_item_groups:{profile}")
	cache.delete_value(f"pos_profile_allowed_item_groups:{profile}")
