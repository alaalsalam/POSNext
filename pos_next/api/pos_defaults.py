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


def _default_customer(profile):
	company = profile.company
	customer_group = _company_group(
		"Customer Group",
		"customer_group_name",
		"parent_customer_group",
		"عملاء نقطة البيع",
		company,
		_root_group("Customer Group", "parent_customer_group"),
	)
	customer_name = profile.customer if profile.customer and frappe.db.exists("Customer", profile.customer) else f"عميل نقدي · {company}"[:140]
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
			customer.insert(ignore_permissions=True)
		customer_name = customer.name
	elif is_multi_company_site() and frappe.db.has_column("Customer", OWNERSHIP_FIELD):
		# A POS Profile's walk-in customer is part of its company boundary, even
		# on a demo restored from the pre-multi-company catalog.
		frappe.db.set_value(
			"Customer",
			customer_name,
			{"customer_group": customer_group, OWNERSHIP_FIELD: company},
			update_modified=False,
		)

	profile.customer = customer_name
	return customer_name


def _default_item_group(profile):
	if profile.get("item_groups"):
		return None
	group = _company_group(
		"Item Group",
		"item_group_name",
		"parent_item_group",
		"أصناف نقطة البيع",
		profile.company,
		_root_group("Item Group", "parent_item_group"),
	)
	profile.append("item_groups", {"item_group": group})
	return group


def ensure_pos_profile_defaults(doc, method=None):
	"""Make a new POS Profile usable without manual master-data setup.

	An explicitly selected customer or item-group configuration is always kept.
	Only missing pieces receive company-owned defaults.
	"""
	profile = doc if getattr(doc, "doctype", None) == "POS Profile" else frappe.get_doc("POS Profile", doc)
	if not profile.company:
		return

	default_customer = _default_customer(profile)
	default_group = _default_item_group(profile)
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
