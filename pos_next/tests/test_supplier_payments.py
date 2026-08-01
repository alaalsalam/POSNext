from unittest import TestCase
from unittest.mock import MagicMock, call, patch

import frappe

from pos_next.api import purchases


class TestSupplierPayments(TestCase):
	def test_validate_partial_and_full_amounts(self):
		self.assertEqual(purchases._validate_payment_amount(40, 100), 40)
		self.assertEqual(purchases._validate_payment_amount(100, 100), 100)

	def test_rejects_zero_and_overpayment(self):
		with self.assertRaises(frappe.ValidationError):
			purchases._validate_payment_amount(0, 100)
		with self.assertRaises(frappe.ValidationError):
			purchases._validate_payment_amount(100.02, 100)

	@staticmethod
	def _invoice(outstanding=100):
		invoice = frappe._dict(
			name="PINV-TEST-001",
			supplier="SUP-TEST",
			supplier_name="Test Supplier",
			company="Test Company",
			currency="SAR",
			grand_total=100,
			outstanding_amount=outstanding,
			status="Unpaid",
			docstatus=1,
			custom_posnext_pos_profile="POS-TEST",
		)
		invoice.reload = MagicMock()
		return invoice

	@staticmethod
	def _payment(docstatus=0, allocated=40):
		reference = frappe._dict(
			reference_doctype="Purchase Invoice",
			reference_name="PINV-TEST-001",
			outstanding_amount=100,
			allocated_amount=allocated,
		)
		payment = frappe._dict(
			name="ACC-PAY-TEST",
			modified="2026-08-01 10:00:00",
			docstatus=docstatus,
			company="Test Company",
			party_type="Supplier",
			payment_type="Pay",
			paid_amount=allocated,
			paid_from="Cash - TC",
			custom_posnext_pos_profile="POS-TEST",
			references=[reference],
		)
		payment.set_amounts = MagicMock()
		payment.insert = MagicMock()
		payment.submit = MagicMock(side_effect=lambda: payment.update(docstatus=1))
		payment.cancel = MagicMock(side_effect=lambda: payment.update(docstatus=2))
		return payment

	@patch("erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry")
	def test_create_is_exact_and_locks_outstanding(self, get_payment_entry):
		invoice = self._invoice()
		payment = self._payment(allocated=100)
		get_payment_entry.return_value = payment
		database = MagicMock()
		database.get_value.return_value = None
		with (
			patch.object(purchases, "_context", return_value=("POS-TEST", "Test Company")),
			patch.object(purchases, "_get_payable_invoice", return_value=invoice) as payable,
			patch.object(purchases, "assert_company_resource", return_value=frappe._dict(account_type="Cash")),
			patch.object(purchases.frappe, "has_permission", return_value=True),
			patch.dict(purchases.frappe.__dict__, {"db": database}),
		):
			result = purchases.create_supplier_payment(
				invoice.name,
				40,
				paid_from="Cash - TC",
				idempotency_key="payment-test-0001",
				pos_profile="POS-TEST",
			)

		self.assertEqual(payment.references[0].allocated_amount, 40)
		payment.insert.assert_called_once_with(ignore_permissions=False)
		payable.assert_called_once_with(invoice.name, "POS-TEST", "Test Company", lock=True)
		self.assertFalse(result["idempotent_replay"])

	def test_retry_returns_same_payment_without_creating_another(self):
		invoice = self._invoice(60)
		payment = self._payment(allocated=40)
		database = MagicMock()
		database.get_value.return_value = payment.name

		def get_doc(doctype, name, ptype="read"):
			return payment if doctype == "Payment Entry" else invoice

		with (
			patch.object(purchases, "_context", return_value=("POS-TEST", "Test Company")),
			patch.object(purchases, "assert_doc_permission", side_effect=get_doc),
			patch.object(purchases.frappe, "has_permission", return_value=True),
			patch.dict(purchases.frappe.__dict__, {"db": database}),
		):
			result = purchases.create_supplier_payment(
				invoice.name,
				40,
				paid_from="Cash - TC",
				idempotency_key="payment-test-0001",
				pos_profile="POS-TEST",
			)
		self.assertTrue(result["idempotent_replay"])
		payment.insert.assert_not_called()

	def test_retry_key_cannot_be_reused_for_a_different_amount(self):
		invoice = self._invoice(60)
		payment = self._payment(allocated=40)
		database = MagicMock()
		database.get_value.return_value = payment.name

		def get_doc(doctype, name, ptype="read"):
			return payment if doctype == "Payment Entry" else invoice

		with (
			patch.object(purchases, "_context", return_value=("POS-TEST", "Test Company")),
			patch.object(purchases, "assert_doc_permission", side_effect=get_doc),
			patch.object(purchases.frappe, "has_permission", return_value=True),
			patch.dict(purchases.frappe.__dict__, {"db": database}),
			self.assertRaises(frappe.PermissionError),
		):
			purchases.create_supplier_payment(
				invoice.name,
				30,
				paid_from="Cash - TC",
				idempotency_key="payment-test-0001",
				pos_profile="POS-TEST",
			)

	def test_submit_serializes_payment_and_invoice(self):
		invoice = self._invoice(40)
		payment = self._payment(allocated=40)
		with (
			patch.object(purchases, "_context", return_value=("POS-TEST", "Test Company")),
			patch.object(purchases, "lock_document", return_value=frappe._dict(modified=payment.modified, docstatus=0)) as lock,
			patch.object(purchases, "_get_supplier_payment", return_value=payment),
			patch.object(purchases, "_get_payable_invoice", return_value=invoice) as payable,
			patch.object(purchases.frappe, "has_permission", return_value=True),
		):
			result = purchases.submit_supplier_payment(payment.name, payment.modified, "POS-TEST")
		self.assertEqual(lock.call_args_list[0], call("Payment Entry", payment.name, ["name", "modified", "docstatus"]))
		payable.assert_called_once_with(invoice.name, "POS-TEST", "Test Company", lock=True)
		payment.submit.assert_called_once()
		self.assertEqual(result["docstatus"], 1)

	def test_stale_payment_is_rejected_before_submit(self):
		payment = self._payment()
		with (
			patch.object(purchases, "_context", return_value=("POS-TEST", "Test Company")),
			patch.object(purchases, "lock_document", return_value=frappe._dict(modified="newer", docstatus=0)),
			patch.object(purchases, "_get_supplier_payment", return_value=payment),
			patch.object(purchases.frappe, "has_permission", return_value=True),
			self.assertRaises(frappe.TimestampMismatchError),
		):
			purchases.submit_supplier_payment(payment.name, "older", "POS-TEST")
		payment.submit.assert_not_called()
