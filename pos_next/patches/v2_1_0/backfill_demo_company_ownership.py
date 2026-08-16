"""Safely assign legacy demo catalog records after enabling multi-company mode."""

import frappe

from pos_next.api.company_scope import OWNERSHIP_FIELD, is_multi_company_site


def execute():
	"""Backfill only unowned records where one company can be proven.

	POS demo sites historically shared a catalog before company ownership was
	introduced.  Once multi-company mode is enabled, unowned records must be
	hidden (fail closed).  This migration restores the demonstrably owned subset:
	stock location takes precedence, then a uniquely configured POS item group.
	Ambiguous shared products are intentionally left unowned for an administrator
	to duplicate or assign explicitly; they are never exposed to another company.
	"""
	if not is_multi_company_site() or not frappe.db.has_column("Item", OWNERSHIP_FIELD):
		return

	profiles = frappe.get_all("POS Profile", filters={"disabled": 0}, fields=["name", "company", "warehouse"])
	warehouse_companies = {}
	group_companies = {}

	for profile in profiles:
		if profile.warehouse:
			warehouse_companies.setdefault(profile.warehouse, set()).add(profile.company)
		for item_group in frappe.get_all("POS Item Group", filters={"parent": profile.name}, pluck="item_group"):
			group_companies.setdefault(item_group, set()).add(profile.company)

	# A group uniquely assigned to a profile can safely receive that owner.  This
	# also makes the normal Desk experience consistent for legacy demo masters.
	if frappe.db.has_column("Item Group", OWNERSHIP_FIELD):
		for item_group, companies in group_companies.items():
			if len(companies) == 1:
				frappe.db.set_value("Item Group", item_group, OWNERSHIP_FIELD, next(iter(companies)), update_modified=False)

	warehouse_names = list(warehouse_companies)
	stock_companies = {}
	if warehouse_names:
		rows = frappe.db.sql(
			"""
			SELECT item_code, warehouse
			FROM `tabBin`
			WHERE actual_qty != 0 AND warehouse IN %(warehouses)s
			""",
			{"warehouses": warehouse_names},
			as_dict=True,
		)
		for row in rows:
			stock_companies.setdefault(row.item_code, set()).update(warehouse_companies[row.warehouse])

	for item in frappe.get_all(
		"Item",
		fields=["name", "item_group", OWNERSHIP_FIELD],
		limit_page_length=0,
	):
		# A uniquely assigned POS Item Group is explicit merchandising intent, so
		# it wins over stock left behind in a shared demo warehouse.  Stock is only
		# used when the group itself does not establish an owner.
		group_owners = group_companies.get(item.item_group, set())
		stock_owners = stock_companies.get(item.name, set())
		owners = group_owners if len(group_owners) == 1 else stock_owners
		if len(owners) == 1:
			owner = next(iter(owners))
			if item.get(OWNERSHIP_FIELD) != owner:
				frappe.db.set_value("Item", item.name, OWNERSHIP_FIELD, owner, update_modified=False)

	frappe.clear_cache()
