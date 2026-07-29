from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from pos_next.api import purchases


class TestSupplierPayments(FrappeTestCase):
	def test_validate_partial_and_full_amounts(self):
		self.assertEqual(purchases._validate_payment_amount(40, 100), 40)
		self.assertEqual(purchases._validate_payment_amount(100, 100), 100)

	def test_rejects_zero_and_overpayment(self):
		with self.assertRaises(frappe.ValidationError):
			purchases._validate_payment_amount(0, 100)
		with self.assertRaises(frappe.ValidationError):
			purchases._validate_payment_amount(100.02, 100)

	def _invoice(self, outstanding=100):
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
		)
		invoice.reload = MagicMock()
		return invoice

	def _account(self):
		return frappe._dict(
			name="Cash - TC",
			company="Test Company",
			is_group=0,
			disabled=0,
			account_type="Cash",
		)

	@patch("erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry")
	def test_creates_draft_payment_with_invoice_reference(self, get_payment_entry):
		invoice = self._invoice()
		reference = frappe._dict(outstanding_amount=100, allocated_amount=100)
		payment = frappe._dict(name="ACC-PAY-TEST", docstatus=0, references=[reference])
		payment.set_amounts = MagicMock()
		payment.insert = MagicMock()
		payment.submit = MagicMock()
		get_payment_entry.return_value = payment

		with (
			patch.object(purchases, "_get_payable_invoice", return_value=invoice),
			patch.object(purchases.frappe, "has_permission", return_value=True),
			patch.object(purchases.frappe, "get_doc", return_value=self._account()),
		):
			result = purchases.create_supplier_payment(
				"PINV-TEST-001", 40, paid_from="Cash - TC", submit=0
			)

		self.assertEqual(reference.allocated_amount, 40)
		payment.insert.assert_called_once_with(ignore_permissions=False)
		payment.submit.assert_not_called()
		self.assertEqual(result["name"], "ACC-PAY-TEST")

	@patch("erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry")
	def test_submits_full_payment_when_authorized(self, get_payment_entry):
		invoice = self._invoice()
		reference = frappe._dict(outstanding_amount=100, allocated_amount=100)
		payment = frappe._dict(name="ACC-PAY-TEST", docstatus=1, references=[reference])
		payment.set_amounts = MagicMock()
		payment.insert = MagicMock()
		payment.submit = MagicMock()
		get_payment_entry.return_value = payment

		with (
			patch.object(purchases, "_get_payable_invoice", return_value=invoice),
			patch.object(purchases.frappe, "has_permission", return_value=True),
			patch.object(purchases.frappe, "get_doc", return_value=self._account()),
		):
			result = purchases.create_supplier_payment(
				"PINV-TEST-001", 100, paid_from="Cash - TC", submit=1
			)

		payment.submit.assert_called_once()
		self.assertEqual(reference.allocated_amount, 100)
		self.assertEqual(result["docstatus"], 1)

	def test_denies_user_without_payment_entry_create_permission(self):
		def deny_payment_entry(doctype, ptype, **kwargs):
			if doctype == "Payment Entry" and ptype == "create":
				raise frappe.PermissionError
			return True

		with patch.object(purchases.frappe, "has_permission", side_effect=deny_payment_entry):
			with self.assertRaises(frappe.PermissionError):
				purchases.create_supplier_payment(
					"PINV-TEST-001", 25, paid_from="Cash - TC", submit=0
				)

	def test_submits_existing_supplier_payment_draft(self):
		payment = frappe._dict(
			name="ACC-PAY-TEST",
			party_type="Supplier",
			payment_type="Pay",
			docstatus=0,
		)
		payment.submit = MagicMock(side_effect=lambda: payment.update({"docstatus": 1}))
		with (
			patch.object(purchases.frappe, "has_permission", return_value=True),
			patch.object(purchases.frappe, "get_doc", return_value=payment),
		):
			result = purchases.submit_supplier_payment(payment.name)
		payment.submit.assert_called_once()
		self.assertEqual(result["docstatus"], 1)

	def test_rejects_non_supplier_payment(self):
		payment = frappe._dict(
			name="ACC-PAY-TEST",
			party_type="Customer",
			payment_type="Receive",
			docstatus=0,
		)
		with (
			patch.object(purchases.frappe, "has_permission", return_value=True),
			patch.object(purchases.frappe, "get_doc", return_value=payment),
			self.assertRaises(frappe.ValidationError),
		):
			purchases.submit_supplier_payment(payment.name)
