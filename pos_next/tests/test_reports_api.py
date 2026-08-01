# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

import json
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from pos_next.api import reports


class TestReportsAPI(FrappeTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		authorize = patch.object(reports, "authorize_report", return_value=frappe._dict())
		authorize.start()
		self.addCleanup(authorize.stop)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_date_ranges_and_invalid_custom_order(self):
		fd, td = reports._date_range("today")
		self.assertEqual(fd, td)
		self.assertEqual(reports._date_range("custom", "2026-01-01", "2026-01-31"), ("2026-01-01", "2026-01-31"))
		with self.assertRaises(frappe.ValidationError):
			reports._date_range("custom", "2026-02-01", "2026-01-01")

	@patch.object(reports.frappe.db, "get_value", return_value="Digit LLC")
	@patch.object(reports.frappe, "get_all", return_value=[])
	def test_invoice_query_uses_erpnext_16_date_and_time_fields(self, get_all, _get_value):
		reports._get_invoice_names("Profile A", "2026-01-01", "2026-01-31")
		kwargs = get_all.call_args.kwargs
		self.assertIn("posting_date", kwargs["fields"])
		self.assertIn("posting_time", kwargs["fields"])
		self.assertNotIn("posting_datetime", kwargs["fields"])
		self.assertEqual(kwargs["order_by"], "posting_date desc, posting_time desc, name desc")
		self.assertEqual(kwargs["filters"]["company"], "Digit LLC")

	@patch.object(reports.frappe.db, "get_value", return_value="SAR")
	@patch.object(reports, "_get_invoice_names")
	def test_daily_summary_reconciles_to_erpnext_totals(self, invoice_query, _get_value):
		invoice_query.return_value = [
			frappe._dict(
				is_return=0, grand_total=115, net_total=100, total_taxes_and_charges=15,
				rounding_adjustment=-0.05, outstanding_amount=15,
			),
			frappe._dict(
				is_return=1, grand_total=-23, net_total=-20, total_taxes_and_charges=-3,
				rounding_adjustment=0, outstanding_amount=0,
			),
		]
		result = reports.get_daily_summary("Profile A")
		self.assertEqual(result["sales_total"], 115)
		self.assertEqual(result["returns_total"], 23)
		self.assertEqual(result["net_sales"], 92)
		self.assertEqual(result["net_total"], 80)
		self.assertEqual(result["tax_total"], 12)
		self.assertEqual(result["outstanding_total"], 15)
		self.assertTrue(result["reconciled"])
		self.assertEqual(result["reconciliation_difference"], 0)

	@patch.object(reports.frappe, "get_all")
	@patch.object(reports, "_get_invoice_names")
	def test_payment_breakdown_uses_paid_total_and_unique_invoice_count(self, invoice_query, get_all):
		invoice_query.return_value = [
			frappe._dict(name="SI-1", grand_total=600, paid_amount=600, outstanding_amount=0),
			frappe._dict(name="SI-2", grand_total=400, paid_amount=400, outstanding_amount=0),
		]
		get_all.return_value = [
			frappe._dict(parent="SI-1", mode_of_payment="Cash", amount=500),
			frappe._dict(parent="SI-1", mode_of_payment="Cash", amount=100),
			frappe._dict(parent="SI-2", mode_of_payment="Card", amount=400),
		]
		result = reports.get_payment_breakdown("Profile A")
		methods = {row["mode"]: row for row in result["methods"]}
		self.assertEqual(methods["Cash"]["count"], 1)
		self.assertEqual(methods["Cash"]["percentage"], 60)
		self.assertEqual(methods["Card"]["percentage"], 40)
		self.assertEqual(result["invoice_total"], 1000)
		self.assertEqual(result["paid_total"], 1000)

	@patch.object(reports.frappe.db, "get_value", return_value="Digit LLC")
	@patch.object(reports.frappe, "get_all")
	def test_recent_transactions_builds_datetime_without_database_column(self, get_all, _get_value):
		get_all.side_effect = [
			[
				frappe._dict(
					name="SI-1", posting_date="2026-07-30", posting_time="14:05:00",
				)
			],
			[frappe._dict(parent="SI-1", mode_of_payment="Cash", amount=10)],
		]
		result = reports.get_recent_transactions("Profile A")
		invoice = result["transactions"][0]
		self.assertEqual(invoice.payment_method, "Cash")
		self.assertTrue(invoice.posting_datetime.startswith("2026-07-30 14:05:00"))
		invoice_call = get_all.call_args_list[0]
		self.assertNotIn("posting_datetime", invoice_call.kwargs["fields"])

	@patch.object(reports, "get_reportable_profiles")
	def test_filters_only_return_pre_authorized_profiles(self, profiles):
		profiles.return_value = [frappe._dict(name="Profile A", company="Company A", currency="SAR")]
		result = reports.get_report_filters()
		self.assertEqual([row.name for row in result["pos_profiles"]], ["Profile A"])
		self.assertEqual(len(result["desk_reports"]), 5)

	def test_demo_acceptance_fixture_reconciles(self):
		fixture_path = Path(__file__).parent / "fixtures" / "reports_acceptance.json"
		fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
		invoices = fixture["invoices"]
		actual = {
			"sales_total": sum(row["grand_total"] for row in invoices if not row["is_return"]),
			"returns_total": sum(abs(row["grand_total"]) for row in invoices if row["is_return"]),
			"net_sales": sum(row["grand_total"] for row in invoices),
			"net_total": sum(row["net_total"] for row in invoices),
			"tax_total": sum(row["total_taxes_and_charges"] for row in invoices),
			"outstanding_total": sum(max(row["outstanding_amount"], 0) for row in invoices if not row["is_return"]),
			"reconciliation_difference": sum(
				row["grand_total"] - row["net_total"] - row["total_taxes_and_charges"]
				for row in invoices
			),
		}
		self.assertEqual(actual, fixture["expected"])
