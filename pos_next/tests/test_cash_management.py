# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

"""Unit tests for the cash management vouchers module.

Mock-based (no DB writes) to match the app's test convention (test_feature_flags,
test_supplier_payments): the whitelisted APIs are exercised at their logic boundary
with the DB / permission layer patched, so the tests run anywhere and never touch
the live site's data. Behavioral end-to-end GL posting is verified separately.

Covers:
  - POS Expense Type controller validations (account root_type / company / group / unique).
  - create_cash_entry input validation + the debit/credit account assembly and party routing
    for every entry type (Expense / Receipt / Payment / Transfer).
  - approve / reject manager gating; feature-flag bypass protection; party & account guards.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

import frappe

from pos_next.api import cash_management as cm
from pos_next.pos_next.doctype.pos_expense_type.pos_expense_type import POSExpenseType


def _throw(msg, exc=None, **kwargs):
	raise (exc or frappe.ValidationError)(msg)


class TestPOSExpenseTypeValidation(TestCase):
	"""The doctype only accepts a non-group, enabled Expense account of its own company,
	and enforces a unique type name per company."""

	@staticmethod
	def _doc(**overrides):
		doc = frappe._dict(
			name="EXP-00001",
			expense_type_name="Fuel",
			company="Test Company",
			expense_account="Fuel Expense - TC",
		)
		doc.update(overrides)
		return doc

	def _validate(self, account_row, duplicate=None):
		database = MagicMock()
		database.get_value.return_value = account_row
		database.exists.return_value = duplicate
		with (
			patch.dict(cm.frappe.__dict__, {"db": database}),
			patch("pos_next.pos_next.doctype.pos_expense_type.pos_expense_type.frappe.db", database),
			patch(
				"pos_next.pos_next.doctype.pos_expense_type.pos_expense_type.frappe.throw",
				side_effect=_throw,
			),
		):
			POSExpenseType.validate(self._doc())

	def test_accepts_a_valid_expense_account(self):
		self._validate(
			frappe._dict(company="Test Company", root_type="Expense", is_group=0, disabled=0)
		)

	def test_rejects_missing_account(self):
		with self.assertRaises(frappe.ValidationError):
			self._validate(None)

	def test_rejects_account_of_another_company(self):
		with self.assertRaises(frappe.ValidationError):
			self._validate(
				frappe._dict(company="Other Company", root_type="Expense", is_group=0, disabled=0)
			)

	def test_rejects_non_expense_account(self):
		with self.assertRaises(frappe.ValidationError):
			self._validate(
				frappe._dict(company="Test Company", root_type="Asset", is_group=0, disabled=0)
			)

	def test_rejects_group_or_disabled_account(self):
		with self.assertRaises(frappe.ValidationError):
			self._validate(
				frappe._dict(company="Test Company", root_type="Expense", is_group=1, disabled=0)
			)
		with self.assertRaises(frappe.ValidationError):
			self._validate(
				frappe._dict(company="Test Company", root_type="Expense", is_group=0, disabled=1)
			)

	def test_rejects_duplicate_name_in_same_company(self):
		with self.assertRaises(frappe.ValidationError):
			self._validate(
				frappe._dict(company="Test Company", root_type="Expense", is_group=0, disabled=0),
				duplicate="EXP-00002",
			)


class TestCreateCashEntryValidation(TestCase):
	"""Input validation happens before any ledger work."""

	def _call(self, **kwargs):
		params = dict(
			entry_type="Receipt",
			amount=10,
			pos_profile="POS-TEST",
			remarks="note",
			idempotency_key="cash-entry-test-0001",
		)
		params.update(kwargs)
		with (
			patch.object(cm, "_cash_context", return_value=("POS-TEST", "Test Company")),
			patch.object(cm.frappe, "has_permission", return_value=True),
			patch.object(cm, "_resolve_cash_box", return_value="Cash Box - TC"),
			patch.object(cm, "_default_cash_account", return_value="Cash Box - TC"),
			patch.object(cm.frappe, "throw", side_effect=_throw),
		):
			return cm.create_cash_entry(**params)

	def test_rejects_unknown_entry_type(self):
		with self.assertRaises(frappe.ValidationError):
			self._call(entry_type="Bogus")

	def test_rejects_zero_or_negative_amount(self):
		with self.assertRaises(frappe.ValidationError):
			self._call(entry_type="Receipt", amount=0)
		with self.assertRaises(frappe.ValidationError):
			self._call(entry_type="Receipt", amount=-5)

	def test_expense_requires_a_note(self):
		with self.assertRaises(frappe.ValidationError):
			self._call(entry_type="Expense", remarks="", expense_type="EXP-1")

	def test_payment_requires_a_note(self):
		with self.assertRaises(frappe.ValidationError):
			self._call(entry_type="Payment", remarks="   ")

	def test_transfer_source_and_destination_must_differ(self):
		with (
			patch.object(cm, "assert_company_resource", return_value=frappe._dict(name="Cash Box - TC", account_type="Cash")),
		):
			with self.assertRaises(frappe.ValidationError):
				self._call(entry_type="Transfer", to_account="Cash Box - TC")

	def test_transfer_destination_must_be_cash_or_bank(self):
		with (
			patch.object(cm, "assert_company_resource", return_value=frappe._dict(name="Debtors - TC", account_type="Receivable")),
		):
			with self.assertRaises(frappe.ValidationError):
				self._call(entry_type="Transfer", to_account="Debtors - TC")

	def test_rejects_party_type_not_allowed_for_entry(self):
		# Receipt allows Customer only; an Employee party must be rejected.
		with self.assertRaises(frappe.ValidationError):
			self._call(entry_type="Receipt", party_type="Employee", party="HR-EMP-1")

	def test_general_receipt_account_cannot_be_the_drawer(self):
		with (
			patch.object(cm, "assert_company_resource", return_value=frappe._dict(name="Cash Box - TC", account_type="Cash")),
		):
			with self.assertRaises(frappe.ValidationError):
				self._call(entry_type="Receipt", account="Cash Box - TC")

	def test_general_receipt_cannot_disguise_a_cash_transfer(self):
		with patch.object(
			cm,
			"assert_company_resource",
			return_value=frappe._dict(name="Bank Box - TC", account_type="Bank"),
		):
			with self.assertRaises(frappe.ValidationError):
				self._call(entry_type="Receipt", account="Bank Box - TC")

	def test_rejects_an_invalid_or_missing_retry_key(self):
		with self.assertRaises(frappe.ValidationError):
			self._call(idempotency_key="short")

	def test_retry_key_fingerprint_rejects_a_different_cash_request(self):
		journal = frappe._dict(custom_posnext_request_fingerprint="a" * 64)
		with (
			patch.object(cm.frappe, "throw", side_effect=_throw),
			self.assertRaises(frappe.ValidationError),
		):
			cm._assert_cash_request_fingerprint(journal, "b" * 64)


class TestCreateCashEntryPosting(TestCase):
	"""The debit/credit accounts and party routing are assembled correctly per type.
	Posting mode is forced to After Approval so the entry stays a draft (no submit)."""

	def _create(self, party_account="Debtors - TC", **kwargs):
		kwargs.setdefault("idempotency_key", "cash-entry-test-0001")
		captured = {}
		journal = MagicMock()
		journal.name = "ACC-JV-TEST-0001"
		journal.docstatus = 0
		journal.posting_date = "2026-08-08"

		def get_doc(payload):
			captured.update(payload)
			journal.accounts = payload["accounts"]
			journal.posa_cash_entry_type = payload["posa_cash_entry_type"]
			journal.user_remark = payload["user_remark"]
			return journal

		database = MagicMock()
		database.get_value.side_effect = lambda doctype, *_args, **_kwargs: (
			None if doctype == "Journal Entry" else "Main - TC"
		)  # No replay exists; Company returns the cost center.

		with (
			patch.object(cm, "_cash_context", return_value=("POS-TEST", "Test Company")),
			patch.object(cm.frappe, "has_permission", return_value=True),
			patch.object(cm, "_resolve_cash_box", return_value="Cash Box - TC"),
			patch.object(cm, "_default_cash_account", return_value="Cash Box - TC"),
			patch.object(cm, "_current_shift", return_value="SHIFT-1"),
			patch.object(cm, "_posting_mode", return_value="After Approval"),
			patch.object(cm, "nowdate", return_value="2026-08-08"),
			patch.object(cm, "_resolve_expense_account", return_value="Fuel Expense - TC"),
			patch.object(cm, "_resolve_party_account", return_value=party_account),
			patch.object(cm, "assert_doc_permission", return_value=None),
			patch.object(
				cm,
				"assert_company_resource",
				return_value=frappe._dict(name="Bank Box - TC", account_type="Bank"),
			),
			patch.dict(cm.frappe.__dict__, {"db": database}),
			patch.object(cm.frappe, "get_doc", side_effect=get_doc),
		):
			result = cm.create_cash_entry(**kwargs)
		return result, captured["accounts"]

	@staticmethod
	def _rows(accounts):
		debit = next(a for a in accounts if a["debit_in_account_currency"])
		credit = next(a for a in accounts if a["credit_in_account_currency"])
		return debit, credit

	def test_expense_debits_the_expense_account_and_credits_cash(self):
		result, accounts = self._create(
			entry_type="Expense", amount=40, pos_profile="POS-TEST", expense_type="EXP-1", remarks="fuel"
		)
		debit, credit = self._rows(accounts)
		self.assertEqual(debit["account"], "Fuel Expense - TC")
		self.assertEqual(credit["account"], "Cash Box - TC")
		self.assertEqual(debit["debit_in_account_currency"], 40)
		self.assertEqual(result["status"], "Pending Approval")

	def test_receipt_from_customer_debits_cash_credits_debtors_with_party(self):
		result, accounts = self._create(
			entry_type="Receipt", amount=200, pos_profile="POS-TEST",
			party_type="Customer", party="CUST-1",
		)
		debit, credit = self._rows(accounts)
		self.assertEqual(debit["account"], "Cash Box - TC")  # money into the drawer
		self.assertEqual(credit["account"], "Debtors - TC")
		# Party attaches to the counter (non-cash) row only.
		self.assertEqual((credit.get("party_type"), credit.get("party")), ("Customer", "CUST-1"))
		self.assertNotIn("party", debit)

	def test_payment_to_employee_debits_creditors_credits_cash_with_party(self):
		result, accounts = self._create(
			party_account="Creditors - TC",
			entry_type="Payment", amount=75, pos_profile="POS-TEST",
			party_type="Employee", party="HR-EMP-1", remarks="advance",
		)
		debit, credit = self._rows(accounts)
		self.assertEqual(debit["account"], "Creditors - TC")
		self.assertEqual(credit["account"], "Cash Box - TC")  # money out of the drawer
		self.assertEqual((debit.get("party_type"), debit.get("party")), ("Employee", "HR-EMP-1"))
		self.assertNotIn("party", credit)

	def test_transfer_debits_destination_credits_source_box(self):
		result, accounts = self._create(
			entry_type="Transfer", amount=500, pos_profile="POS-TEST", to_account="Bank Box - TC"
		)
		debit, credit = self._rows(accounts)
		self.assertEqual(debit["account"], "Bank Box - TC")  # into the destination
		self.assertEqual(credit["account"], "Cash Box - TC")  # out of the source drawer

	def test_immediate_mode_submits_the_entry(self):
		journal = MagicMock()
		journal.name = "ACC-JV-TEST-0002"
		journal.docstatus = 1
		journal.posting_date = "2026-08-08"
		database = MagicMock()
		database.get_value.side_effect = lambda doctype, *_args, **_kwargs: (
			None if doctype == "Journal Entry" else "Main - TC"
		)
		journal.posa_cash_entry_type = "Expense"
		journal.user_remark = "fuel"
		with (
			patch.object(cm, "_cash_context", return_value=("POS-TEST", "Test Company")),
			patch.object(cm.frappe, "has_permission", return_value=True),
			patch.object(cm, "_resolve_cash_box", return_value="Cash Box - TC"),
			patch.object(cm, "_default_cash_account", return_value="Cash Box - TC"),
			patch.object(cm, "_current_shift", return_value="SHIFT-1"),
			patch.object(cm, "_posting_mode", return_value="Immediate"),
			patch.object(cm, "nowdate", return_value="2026-08-08"),
			patch.object(cm, "_resolve_expense_account", return_value="Fuel Expense - TC"),
			patch.dict(cm.frappe.__dict__, {"db": database}),
			patch.object(cm.frappe, "get_doc", return_value=journal),
		):
			result = cm.create_cash_entry(
				entry_type="Expense", amount=40, pos_profile="POS-TEST", expense_type="EXP-1", remarks="fuel",
				idempotency_key="cash-entry-test-0001",
			)
		journal.submit.assert_called_once()
		self.assertEqual(result["status"], "Approved")


class TestCashEntryManagerGating(TestCase):
	"""approve / reject are manager-only and act only on drafts."""

	def test_approve_denied_to_non_manager_before_submit(self):
		with (
			patch.object(cm, "_cash_context", return_value=("POS-TEST", "Test Company")),
			patch.object(cm.frappe, "has_permission", side_effect=frappe.PermissionError) as permission,
			patch.object(cm.frappe, "throw", side_effect=_throw),
			patch.object(cm, "_get_cash_entry") as get_entry,
			self.assertRaises(frappe.PermissionError),
		):
			cm.approve_cash_entry("ACC-JV-1", pos_profile="POS-TEST")
		permission.assert_called_once_with("Journal Entry", "cancel", throw=True)
		get_entry.assert_not_called()

	def test_reject_denied_to_non_manager_before_delete(self):
		with (
			patch.object(cm, "_cash_context", return_value=("POS-TEST", "Test Company")),
			patch.object(cm.frappe, "has_permission", side_effect=frappe.PermissionError) as permission,
			patch.object(cm.frappe, "throw", side_effect=_throw),
			patch.object(cm, "_get_cash_entry") as get_entry,
			self.assertRaises(frappe.PermissionError),
		):
			cm.reject_cash_entry("ACC-JV-1", pos_profile="POS-TEST")
		permission.assert_called_once_with("Journal Entry", "delete", throw=True)
		get_entry.assert_not_called()

	def test_approve_rejects_an_already_posted_entry(self):
		posted = frappe._dict(name="ACC-JV-1", docstatus=1)
		with (
			patch.object(cm, "_cash_context", return_value=("POS-TEST", "Test Company")),
			patch.object(cm.frappe, "has_permission", return_value=True),
			patch.object(cm, "_get_cash_entry", return_value=posted),
			patch.object(cm.frappe, "throw", side_effect=_throw),
			self.assertRaises(frappe.ValidationError),
		):
			cm.approve_cash_entry("ACC-JV-1", pos_profile="POS-TEST")

	def test_approve_submits_a_pending_draft(self):
		draft = MagicMock()
		draft.name = "ACC-JV-1"
		draft.docstatus = 0
		with (
			patch.object(cm, "_cash_context", return_value=("POS-TEST", "Test Company")),
			patch.object(cm.frappe, "has_permission", return_value=True),
			patch.object(cm, "_get_cash_entry", return_value=draft),
		):
			draft.submit.side_effect = lambda: setattr(draft, "docstatus", 1)
			result = cm.approve_cash_entry("ACC-JV-1", pos_profile="POS-TEST")
		draft.submit.assert_called_once()
		self.assertEqual(result["status"], "Approved")

	def test_cash_entry_without_a_shift_cannot_be_accessed_by_name(self):
		journal = frappe._dict(
			company="Test Company",
			posa_cash_entry_type="Expense",
			posa_pos_opening_shift=None,
		)
		with (
			patch.object(cm, "assert_doc_permission", return_value=journal),
			patch.object(cm.frappe, "throw", side_effect=_throw),
			self.assertRaises(frappe.PermissionError),
		):
			cm._get_cash_entry("ACC-JV-1", "POS-TEST", "Test Company")


class TestCashManagementFeatureGating(TestCase):
	"""Every endpoint refuses when the feature flag is off, before any permission/DB work."""

	def test_create_cash_entry_cannot_bypass_disabled_flag(self):
		with (
			patch.object(cm, "_cash_context", side_effect=frappe.PermissionError),
			patch.object(cm.frappe, "has_permission") as permission,
			self.assertRaises(frappe.PermissionError),
		):
			cm.create_cash_entry(entry_type="Receipt", amount=10, pos_profile="POS-TEST")
		permission.assert_not_called()

	def test_get_cash_entries_cannot_bypass_disabled_flag(self):
		with (
			patch.object(cm, "_cash_context", side_effect=frappe.PermissionError),
			patch.object(cm.frappe, "has_permission") as permission,
			self.assertRaises(frappe.PermissionError),
		):
			cm.get_cash_entries(pos_profile="POS-TEST")
		permission.assert_not_called()

	def test_get_parties_rejects_unknown_party_type(self):
		with (
			patch.object(cm, "_cash_context", return_value=("POS-TEST", "Test Company")),
			patch.object(cm.frappe, "throw", side_effect=_throw),
			self.assertRaises(frappe.ValidationError),
		):
			cm.get_parties("Supplier", pos_profile="POS-TEST")

	def test_get_cash_entry_accounts_only_for_receipt_or_payment(self):
		with (
			patch.object(cm, "_cash_context", return_value=("POS-TEST", "Test Company")),
			patch.object(cm.frappe, "has_permission", return_value=True),
			patch.object(cm.frappe, "throw", side_effect=_throw),
			self.assertRaises(frappe.ValidationError),
		):
			cm.get_cash_entry_accounts("Expense", pos_profile="POS-TEST")


class TestExpenseTypeManagement(TestCase):
	"""Expense-type CRUD is feature- and native-permission-gated and cannot cross companies."""

	def test_list_rejected_when_flag_off_or_not_manager(self):
		# Feature or native permission failure must exit before any later work.
		with (
			patch.object(cm, "_assert_cash_manager", side_effect=frappe.PermissionError),
			patch.object(cm.frappe, "has_permission") as permission,
			self.assertRaises(frappe.PermissionError),
		):
			cm.get_expense_types(pos_profile="POS-TEST")
		permission.assert_not_called()

	def test_save_rejected_when_flag_off_or_not_manager(self):
		with (
			patch.object(cm, "_assert_cash_manager", side_effect=frappe.PermissionError),
			patch.object(cm.frappe, "get_doc") as get_doc,
			self.assertRaises(frappe.PermissionError),
		):
			cm.save_expense_type("Fuel", "Fuel Expense - TC", pos_profile="POS-TEST")
		get_doc.assert_not_called()

	def test_delete_rejected_when_flag_off_or_not_manager(self):
		with (
			patch.object(cm, "_assert_cash_manager", side_effect=frappe.PermissionError),
			patch.object(cm.frappe, "delete_doc") as delete_doc,
			self.assertRaises(frappe.PermissionError),
		):
			cm.delete_expense_type("EXP-9", pos_profile="POS-TEST")
		delete_doc.assert_not_called()

	def test_save_requires_a_name_and_account(self):
		with (
			patch.object(cm, "_assert_cash_manager", return_value=("POS-TEST", "Test Company")),
			patch.object(cm.frappe, "throw", side_effect=_throw),
		):
			with self.assertRaises(frappe.ValidationError):
				cm.save_expense_type("   ", "Fuel Expense - TC", pos_profile="POS-TEST")
			with self.assertRaises(frappe.ValidationError):
				cm.save_expense_type("Fuel", "", pos_profile="POS-TEST")

	def test_edit_cannot_cross_company(self):
		database = MagicMock()
		database.get_value.return_value = "Other Company"  # existing type's company
		with (
			patch.object(cm, "_assert_cash_manager", return_value=("POS-TEST", "Test Company")),
			patch.dict(cm.frappe.__dict__, {"db": database}),
			patch.object(cm.frappe, "get_doc") as get_doc,
			patch.object(cm.frappe, "throw", side_effect=_throw),
			self.assertRaises(frappe.PermissionError),
		):
			cm.save_expense_type("Fuel", "Fuel Expense - TC", pos_profile="POS-TEST", name="EXP-9")
		get_doc.assert_not_called()

	def test_new_type_is_bound_to_the_profile_company(self):
		created = {}
		doc = MagicMock()
		doc.name = "EXP-00007"
		doc.expense_type_name = "Fuel"
		doc.expense_account = "Fuel Expense - TC"
		doc.enabled = 1

		def get_doc(payload):
			created.update(payload)
			return doc

		with (
			patch.object(cm, "_assert_cash_manager", return_value=("POS-TEST", "Test Company")),
			patch.object(cm.frappe, "get_doc", side_effect=get_doc),
		):
			result = cm.save_expense_type("Fuel", "Fuel Expense - TC", pos_profile="POS-TEST", enabled=1)
		self.assertEqual(created["company"], "Test Company")
		doc.insert.assert_called_once()
		self.assertEqual(result["name"], "EXP-00007")

	def test_delete_cannot_cross_company(self):
		database = MagicMock()
		database.get_value.return_value = "Other Company"
		with (
			patch.object(cm, "_assert_cash_manager", return_value=("POS-TEST", "Test Company")),
			patch.dict(cm.frappe.__dict__, {"db": database}),
			patch.object(cm.frappe, "delete_doc") as delete_doc,
			patch.object(cm.frappe, "throw", side_effect=_throw),
			self.assertRaises(frappe.PermissionError),
		):
			cm.delete_expense_type("EXP-9", pos_profile="POS-TEST")
		delete_doc.assert_not_called()

	def test_create_account_gated_before_account_permission(self):
		with (
			patch.object(cm, "_assert_cash_manager", side_effect=frappe.PermissionError),
			patch.object(cm.frappe, "has_permission") as permission,
			self.assertRaises(frappe.PermissionError),
		):
			cm.create_expense_account("Electricity", pos_profile="POS-TEST")
		permission.assert_not_called()

	def test_create_account_requires_a_name(self):
		with (
			patch.object(cm, "_assert_cash_manager", return_value=("POS-TEST", "Test Company")),
			patch.object(cm.frappe, "has_permission", return_value=True),
			patch.object(cm.frappe, "throw", side_effect=_throw),
			self.assertRaises(frappe.ValidationError),
		):
			cm.create_expense_account("   ", pos_profile="POS-TEST")

	def test_create_account_rejects_duplicate_name(self):
		database = MagicMock()
		database.exists.return_value = "Electricity - TC"
		with (
			patch.object(cm, "_assert_cash_manager", return_value=("POS-TEST", "Test Company")),
			patch.object(cm.frappe, "has_permission", return_value=True),
			patch.dict(cm.frappe.__dict__, {"db": database}),
			patch.object(cm.frappe, "throw", side_effect=_throw),
			self.assertRaises(frappe.ValidationError),
		):
			cm.create_expense_account("Electricity", pos_profile="POS-TEST")

	def test_create_account_marks_it_as_a_pos_expense_account(self):
		created = {}
		doc = MagicMock()
		doc.name = "Electricity - TC"
		doc.account_name = "Electricity"

		def get_doc(payload):
			created.update(payload)
			return doc

		database = MagicMock()
		database.exists.return_value = None
		with (
			patch.object(cm, "_assert_cash_manager", return_value=("POS-TEST", "Test Company")),
			patch.object(cm.frappe, "has_permission", return_value=True),
			patch.dict(cm.frappe.__dict__, {"db": database}),
			patch.object(cm, "_expense_parent_group", return_value="Indirect Expenses - TC"),
			patch.object(cm.frappe, "get_doc", side_effect=get_doc),
		):
			result = cm.create_expense_account("Electricity", pos_profile="POS-TEST")
		self.assertEqual(created["custom_pos_expense_account"], 1)
		self.assertEqual(created["root_type"], "Expense")
		self.assertEqual(created["parent_account"], "Indirect Expenses - TC")
		self.assertEqual(created["company"], "Test Company")
		doc.insert.assert_called_once()
		self.assertEqual(result["name"], "Electricity - TC")


class TestCashEntrySummary(TestCase):
	def test_summary_uses_drawer_ledger_effect_and_marks_every_entry(self):
		rows = [
			frappe._dict(name="ACC-JV-1", docstatus=1, posa_cash_entry_type="Receipt"),
			frappe._dict(name="ACC-JV-2", docstatus=1, posa_cash_entry_type="Transfer"),
			frappe._dict(name="ACC-JV-3", docstatus=0, posa_cash_entry_type="Expense"),
		]
		ledger_rows = [
			frappe._dict(debit_in_account_currency=120, credit_in_account_currency=0),
			frappe._dict(debit_in_account_currency=0, credit_in_account_currency=50),
		]
		with (
			patch.object(cm, "_cash_context", return_value=("POS-TEST", "Test Company")),
			patch.object(cm, "_current_shift", return_value="SHIFT-1"),
			patch.object(cm, "_default_cash_account", return_value="Cash - TC"),
			patch.object(cm.frappe, "has_permission", return_value=True),
			patch.object(cm.frappe, "get_list", return_value=rows),
			patch.object(cm.frappe, "get_all", return_value=ledger_rows),
		):
			result = cm.get_cash_entries(pos_profile="POS-TEST")

		self.assertEqual([row.status for row in result["entries"]], ["Approved", "Approved", "Pending Approval"])
		self.assertEqual(result["received_total"], 120)
		self.assertEqual(result["paid_total"], 50)
		self.assertEqual(result["net_total"], 70)
		self.assertEqual(result["pending_count"], 1)
