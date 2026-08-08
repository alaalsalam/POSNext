# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

"""Proves the app's permission model is app-owned: the POSNext Cashier / POS Manager
roles grant the correct two-tier access on their own, WITHOUT any ERPNext role
(Sales User, Stock User, Accounts User, …) attached. Guards the shipped grants in
patches/v2_0_0/ship_pos_role_permissions.py against regression."""

import frappe
from frappe.tests.utils import FrappeTestCase

CASHIER = "test_pos_cashier@example.com"
MANAGER = "test_pos_manager@example.com"

# (doctype, ptype, expected_for_cashier, expected_for_manager)
CONTRACT = [
	("Sales Invoice", "create", True, True),
	("Sales Invoice", "submit", True, True),
	("Payment Entry", "create", True, True),
	("Customer", "create", True, True),
	("Item", "read", True, True),
	# Manager-only capabilities — cashier must stay locked out (no access-widening):
	("Item", "create", False, True),
	("Item", "write", False, True),
	("Promotional Scheme", "read", True, True),
	("Promotional Scheme", "write", False, True),
	("Promotional Scheme", "create", False, True),
	("POS Settings", "write", False, True),
	("Purchase Invoice", "create", False, True),
	("Company", "read", False, True),
	# Cash Management: the cashier records cash movements (Journal Entry) but cannot void them.
	("Journal Entry", "read", True, True),
	("Journal Entry", "create", True, True),
	("Journal Entry", "submit", True, True),
	("Journal Entry", "cancel", False, True),
	# Only a manager may reject (delete) a pending cash entry — the cashier stays locked out.
	("Journal Entry", "delete", False, True),
]


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


class TestAppOwnedRolePermissions(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Ensure the shipped grants are applied (idempotent) so the test is self-contained.
		from pos_next.patches.v2_0_0 import ship_cash_management_permissions, ship_pos_role_permissions

		ship_pos_role_permissions.execute()
		ship_cash_management_permissions.execute()
		_make_user(CASHIER, ["POSNext Cashier"])
		_make_user(MANAGER, ["POSNext Cashier", "POS Manager"])

	@classmethod
	def tearDownClass(cls):
		for email in (CASHIER, MANAGER):
			if frappe.db.exists("User", email):
				frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		super().tearDownClass()

	def _assert_tier(self, user, index):
		frappe.set_user(user)
		try:
			# No ERPNext role should be present — only the app roles (+ auto Desk User).
			roles = set(frappe.get_roles()) - {"All", "Guest", "Desk User", "POSNext Cashier", "POS Manager"}
			self.assertEqual(roles, set(), f"{user} unexpectedly has non-app roles: {roles}")
			for doctype, ptype, exp_cashier, exp_manager in CONTRACT:
				expected = exp_cashier if index == 0 else exp_manager
				got = bool(frappe.has_permission(doctype, ptype))
				self.assertEqual(
					got, expected, f"{user}: {doctype}.{ptype} expected {expected}, got {got}"
				)
		finally:
			frappe.set_user("Administrator")

	def test_cashier_tier_without_erpnext_roles(self):
		self._assert_tier(CASHIER, 0)

	def test_manager_tier_without_erpnext_roles(self):
		self._assert_tier(MANAGER, 1)
