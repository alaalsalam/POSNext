# Copyright (c) 2020, Youssef Restom and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from pos_next.pos_next.doctype.pos_closing_shift import pos_closing_shift as pcs


def _make_closing_shift_doc(
	payment_reconciliation,
	posa_variance_journal_entry=None,
	docstatus=1,
	name="POSA-CS-TEST-0001",
	pos_profile="Test Profile",
	company="Test Company",
	user="cashier@example.com",
):
	doc = MagicMock()
	doc.name = name
	doc.docstatus = docstatus
	doc.pos_profile = pos_profile
	doc.company = company
	doc.user = user
	doc.posa_variance_journal_entry = posa_variance_journal_entry
	doc.payment_reconciliation = [frappe._dict(row) for row in payment_reconciliation]
	return doc


class TestPostCashVariance(FrappeTestCase):
	def setUp(self):
		# Every test patches frappe.has_permission to allow, so permission logic
		# itself is covered by test_permission_denied_propagates below.
		self.permission_patch = patch.object(pcs.frappe, "has_permission", return_value=True)
		self.permission_patch.start()
		self.addCleanup(self.permission_patch.stop)

	def _run(self, doc, settings=None, shortage_account=None, payment_account="Cash - TC", je=None):
		settings = settings or {}
		je = je or MagicMock(name="Journal Entry")

		def get_value_side_effect(doctype, filters=None, fieldname=None, *a, **k):
			if doctype == "POS Settings":
				return settings.get(fieldname)
			if doctype == "User":
				return shortage_account
			return None

		with (
			patch.object(pcs.frappe, "get_doc", return_value=doc),
			patch.object(pcs.frappe.db, "get_value", side_effect=get_value_side_effect),
			patch("pos_next.api.invoices.get_payment_account", return_value={"account": payment_account}),
			patch.object(pcs.frappe, "new_doc", return_value=je),
		):
			result = pcs.post_cash_variance(doc.name)
		return result, je

	def test_shortage_debits_cashier_account_credits_payment_account(self):
		doc = _make_closing_shift_doc([{"mode_of_payment": "Cash", "difference": -50}])
		result, je = self._run(
			doc,
			settings={"posa_max_variance_for_posting": 100, "posa_surplus_account": "Surplus - TC"},
			shortage_account="Cashier Shortage - TC",
		)

		self.assertTrue(result["posted"])
		je.set.assert_called_once()
		accounts = je.set.call_args[0][1]
		self.assertEqual(len(accounts), 2)
		self.assertEqual(accounts[0]["account"], "Cashier Shortage - TC")
		self.assertEqual(accounts[0]["debit_in_account_currency"], 50)
		self.assertEqual(accounts[1]["account"], "Cash - TC")
		self.assertEqual(accounts[1]["credit_in_account_currency"], 50)
		je.submit.assert_called_once()
		doc.db_set.assert_called_once_with("posa_variance_journal_entry", je.name)

	def test_surplus_debits_payment_account_credits_surplus_account(self):
		doc = _make_closing_shift_doc([{"mode_of_payment": "Cash", "difference": 30}])
		result, je = self._run(
			doc,
			settings={"posa_max_variance_for_posting": 100, "posa_surplus_account": "Surplus - TC"},
			shortage_account="Cashier Shortage - TC",
		)

		self.assertTrue(result["posted"])
		accounts = je.set.call_args[0][1]
		self.assertEqual(accounts[0]["account"], "Cash - TC")
		self.assertEqual(accounts[0]["debit_in_account_currency"], 30)
		self.assertEqual(accounts[1]["account"], "Surplus - TC")
		self.assertEqual(accounts[1]["credit_in_account_currency"], 30)

	def test_combined_total_over_cap_blocks_the_whole_shift(self):
		# Cash shortage 40 + Card surplus 70 = 110 combined, cap is 100 — neither
		# should post, even though each is individually under the cap.
		doc = _make_closing_shift_doc(
			[
				{"mode_of_payment": "Cash", "difference": -40},
				{"mode_of_payment": "Card", "difference": 70},
			]
		)
		result, je = self._run(
			doc,
			settings={"posa_max_variance_for_posting": 100, "posa_surplus_account": "Surplus - TC"},
			shortage_account="Cashier Shortage - TC",
		)

		self.assertFalse(result["posted"])
		self.assertEqual(result["reason"], "over_cap")
		self.assertEqual(result["combined_total"], 110)
		je.set.assert_not_called()
		je.submit.assert_not_called()

	def test_missing_shortage_account_is_skipped_not_thrown(self):
		doc = _make_closing_shift_doc([{"mode_of_payment": "Cash", "difference": -20}])
		result, je = self._run(
			doc,
			settings={"posa_max_variance_for_posting": 100, "posa_surplus_account": "Surplus - TC"},
			shortage_account=None,
		)

		self.assertFalse(result["posted"])
		self.assertEqual(result["reason"], "nothing_postable")
		self.assertEqual(result["skipped"], [{"mode_of_payment": "Cash", "reason": "no_shortage_account"}])
		je.submit.assert_not_called()

	def test_zero_cap_disables_posting(self):
		doc = _make_closing_shift_doc([{"mode_of_payment": "Cash", "difference": -5}])
		result, _je = self._run(
			doc,
			settings={"posa_max_variance_for_posting": 0, "posa_surplus_account": "Surplus - TC"},
			shortage_account="Cashier Shortage - TC",
		)
		self.assertFalse(result["posted"])
		self.assertEqual(result["reason"], "over_cap")

	def test_no_difference_short_circuits(self):
		doc = _make_closing_shift_doc([{"mode_of_payment": "Cash", "difference": 0}])
		result, _je = self._run(doc)
		self.assertFalse(result["posted"])
		self.assertEqual(result["reason"], "no_difference")

	def test_already_posted_shift_is_rejected(self):
		doc = _make_closing_shift_doc(
			[{"mode_of_payment": "Cash", "difference": -5}],
			posa_variance_journal_entry="ACC-JV-2026-00001",
		)
		with patch.object(pcs.frappe, "get_doc", return_value=doc):
			with self.assertRaises(frappe.ValidationError):
				pcs.post_cash_variance(doc.name)

	def test_draft_shift_is_rejected(self):
		doc = _make_closing_shift_doc([{"mode_of_payment": "Cash", "difference": -5}], docstatus=0)
		with patch.object(pcs.frappe, "get_doc", return_value=doc):
			with self.assertRaises(frappe.ValidationError):
				pcs.post_cash_variance(doc.name)

	def test_permission_denied_propagates(self):
		# This inner patch on the same target takes precedence over setUp's while
		# active, and cleanly reverts to it afterwards — no manual stop/start needed.
		doc = _make_closing_shift_doc([{"mode_of_payment": "Cash", "difference": -5}])
		with (
			patch.object(pcs.frappe, "get_doc", return_value=doc),
			patch.object(pcs.frappe, "has_permission", side_effect=frappe.PermissionError),
		):
			with self.assertRaises(frappe.PermissionError):
				pcs.post_cash_variance(doc.name)
