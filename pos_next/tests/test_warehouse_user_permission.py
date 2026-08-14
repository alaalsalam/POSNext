# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

"""Regression guard for the in-POS purchase "receiving warehouse" dropdown.

Each POS profile restricts its cashier to a single sales warehouse via a Warehouse User
Permission. With apply_strict_user_permissions on, that permission used to cascade onto
Warehouse's own self-referential Link field `default_in_transit_warehouse` (empty on nearly
every warehouse), which excluded EVERY warehouse from list queries — so get_warehouses returned
zero rows for every restricted user and purchases could not be received anywhere.

patches/v2_0_0/warehouse_transit_ignore_user_perms.py ships a Property Setter that marks that
link `ignore_user_permissions`, mirroring how core already treats `parent_warehouse`. After the
fix the query correctly narrows to the user's permitted warehouse. This test reproduces the
strict-mode condition and asserts the permitted warehouse is returned (not the empty set)."""

import frappe
from frappe.tests.utils import FrappeTestCase

MANAGER = "test_wh_up_manager@example.com"


def _make_user(email, roles):
	if frappe.db.exists("User", email):
		frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": email.split("@")[0],
			"send_welcome_email": 0,
			"roles": [{"role": r} for r in roles],
		}
	)
	user.flags.ignore_permissions = True
	user.insert(ignore_permissions=True)
	return user


def _add_user_permission(user, allow, for_value):
	frappe.get_doc(
		{
			"doctype": "User Permission",
			"user": user,
			"allow": allow,
			"for_value": for_value,
		}
	).insert(ignore_permissions=True)


class TestWarehouseUserPermission(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		from pos_next.patches.v2_0_0 import (
			purchase_flow_ignore_user_perms,
			ship_pos_role_permissions,
			warehouse_transit_ignore_user_perms,
		)

		ship_pos_role_permissions.execute()
		warehouse_transit_ignore_user_perms.execute()
		purchase_flow_ignore_user_perms.execute()

		# Use a real company that has at least one non-group, enabled warehouse.
		cls.warehouse = frappe.db.get_value(
			"Warehouse", {"is_group": 0, "disabled": 0}, ["name", "company"], as_dict=True
		)
		if not cls.warehouse:
			return
		cls.company = cls.warehouse.company

		cls.original_strict = frappe.db.get_single_value(
			"System Settings", "apply_strict_user_permissions"
		)
		frappe.db.set_single_value("System Settings", "apply_strict_user_permissions", 1)
		frappe.clear_cache()

		_make_user(MANAGER, ["POS Cashier", "POS Manager"])
		_add_user_permission(MANAGER, "Company", cls.company)
		_add_user_permission(MANAGER, "Warehouse", cls.warehouse.name)

		# An Item whose item_defaults warehouse is empty (the common case) — under strict user
		# permissions the Warehouse UP used to cascade onto that empty child link and block the
		# cashier from even reading the item on the purchase path.
		cls.item_code = "TEST-POSNEXT-UP-ITEM"
		if frappe.db.exists("Item", cls.item_code):
			frappe.delete_doc("Item", cls.item_code, force=True, ignore_permissions=True)
		item_group = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
		item = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": cls.item_code,
				"item_name": cls.item_code,
				"item_group": item_group,
				"stock_uom": "Nos",
				"is_purchase_item": 1,
				"is_stock_item": 0,
				"company": cls.company,
				"item_defaults": [{"company": cls.company}],  # default_warehouse deliberately empty
			}
		)
		item.flags.ignore_permissions = True
		item.insert(ignore_permissions=True)

	@classmethod
	def tearDownClass(cls):
		if getattr(cls, "warehouse", None):
			frappe.db.set_single_value(
				"System Settings", "apply_strict_user_permissions", cls.original_strict
			)
			frappe.clear_cache()
		if frappe.db.exists("User", MANAGER):
			frappe.delete_doc("User", MANAGER, force=True, ignore_permissions=True)
		if getattr(cls, "item_code", None) and frappe.db.exists("Item", cls.item_code):
			frappe.delete_doc("Item", cls.item_code, force=True, ignore_permissions=True)
		super().tearDownClass()

	def test_permitted_warehouse_is_visible_under_strict_user_permissions(self):
		if not getattr(self, "warehouse", None):
			self.skipTest("no non-group warehouse available in the test database")
		frappe.set_user(MANAGER)
		try:
			rows = frappe.get_list(
				"Warehouse",
				filters={"company": self.company, "is_group": 0, "disabled": 0},
				fields=["name"],
				limit=200,
			)
		finally:
			frappe.set_user("Administrator")
		names = {row.name for row in rows}
		self.assertIn(
			self.warehouse.name,
			names,
			"strict user permissions hid the user's own permitted warehouse — the transit-link "
			"Property Setter is missing or not applied",
		)

	def test_transit_link_property_setter_is_shipped(self):
		value = frappe.db.get_value(
			"Property Setter",
			{
				"doc_type": "Warehouse",
				"field_name": "default_in_transit_warehouse",
				"property": "ignore_user_permissions",
			},
			"value",
		)
		self.assertEqual(value, "1")

	def test_restricted_cashier_can_read_purchase_item_with_empty_default_warehouse(self):
		if not getattr(self, "warehouse", None):
			self.skipTest("no non-group warehouse available in the test database")
		item = frappe.get_doc("Item", self.item_code)
		frappe.set_user(MANAGER)
		try:
			allowed = frappe.has_permission("Item", "read", doc=item)
		finally:
			frappe.set_user("Administrator")
		self.assertTrue(
			allowed,
			"strict user permissions blocked a restricted cashier from reading a purchasable item "
			"because its item_defaults.default_warehouse is empty — the purchase-flow Property "
			"Setters are missing or not applied",
		)

	def test_purchase_flow_property_setters_are_shipped(self):
		for doctype, fieldname in (
			("Item Default", "default_warehouse"),
			("Item Reorder", "warehouse"),
			("Item Reorder", "warehouse_group"),
			("Purchase Invoice", "represents_company"),
		):
			value = frappe.db.get_value(
				"Property Setter",
				{"doc_type": doctype, "field_name": fieldname, "property": "ignore_user_permissions"},
				"value",
			)
			self.assertEqual(value, "1", f"{doctype}.{fieldname} ignore_user_permissions not shipped")
