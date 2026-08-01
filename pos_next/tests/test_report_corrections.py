# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

import re
from datetime import datetime
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from pos_next.api.reporting_utils import (
	add_datetime_bounds,
	inclusive_date_days,
	payment_method_fieldnames,
)
from pos_next.pos_next.report.cashier_performance_report import cashier_performance_report
from pos_next.pos_next.report.offline_sync_and_system_health_report import (
	offline_sync_and_system_health_report,
)
from pos_next.pos_next.report.payments_and_cash_control_report import (
	payments_and_cash_control_report,
)
from pos_next.pos_next.report.sales_vs_shifts_report import sales_vs_shifts_report


class TestReportCorrections(FrappeTestCase):
	def test_datetime_bounds_include_last_second_and_exclude_next_day(self):
		filters = {"from_date": "2026-07-30", "to_date": "2026-07-30"}
		add_datetime_bounds(filters)
		self.assertEqual(filters["from_datetime"], "2026-07-30 00:00:00")
		self.assertEqual(filters["to_datetime_exclusive"], "2026-07-31 00:00:00")
		self.assertLess(
			datetime(2026, 7, 30, 23, 59, 59, 999999),
			datetime.fromisoformat(filters["to_datetime_exclusive"]),
		)

	def test_datetime_reports_use_half_open_upper_bound(self):
		builders = (
			payments_and_cash_control_report.get_conditions,
			cashier_performance_report._build_shift_conditions,
			offline_sync_and_system_health_report.get_conditions,
			sales_vs_shifts_report.build_conditions,
		)
		for builder in builders:
			with self.subTest(builder=builder.__module__):
				filters = {"from_date": "2026-07-01", "to_date": "2026-07-31"}
				conditions = builder(filters)
				self.assertIn(">= %(from_datetime)s", conditions)
				self.assertIn("< %(to_datetime_exclusive)s", conditions)
				self.assertEqual(filters["to_datetime_exclusive"], "2026-08-01 00:00:00")

	def test_inventory_period_is_inclusive_and_one_day_is_one(self):
		self.assertEqual(inclusive_date_days("2026-07-30", "2026-07-30"), 1)
		self.assertEqual(inclusive_date_days("2026-07-01", "2026-07-31"), 31)

	@patch.object(payments_and_cash_control_report.frappe.db, "sql", return_value=[])
	def test_bank_deposit_batch_returns_empty_when_no_deposit(self, sql):
		result = payments_and_cash_control_report._get_bank_deposit_data(
			[frappe._dict(shift="SHIFT-1")]
		)
		self.assertEqual(result, {})
		sql.assert_called_once()

	@patch.object(payments_and_cash_control_report.frappe.db, "sql")
	def test_bank_deposit_batch_maps_multiple_shifts(self, sql):
		sql.return_value = [
			frappe._dict(shift="SHIFT-1", deposit_amount=125.5, deposit_date="2026-07-30"),
			frappe._dict(shift="SHIFT-2", deposit_amount=250, deposit_date="2026-07-31"),
		]
		result = payments_and_cash_control_report._get_bank_deposit_data(
			[frappe._dict(shift="SHIFT-1"), frappe._dict(shift="SHIFT-2")]
		)
		self.assertEqual(result["SHIFT-1"]["deposit_amount"], 125.5)
		self.assertEqual(result["SHIFT-2"]["deposit_date"], "2026-07-31")
		sql.assert_called_once()
		self.assertCountEqual(sql.call_args.args[1], ["SHIFT-1", "SHIFT-2"])

	@patch.object(payments_and_cash_control_report, "_get_bank_deposit_data")
	@patch.object(payments_and_cash_control_report, "_get_transaction_counts")
	@patch.object(payments_and_cash_control_report.frappe.db, "sql")
	def test_shift_rows_merge_deposits_with_defaults_without_n_plus_one(
		self, sql, transaction_counts, deposits
	):
		raw = [
			frappe._dict(
				shift="SHIFT-1", pos_profile="Profile A", cashier="a@example.com",
				posting_date="2026-07-30", shift_start="08:00", shift_end="16:00",
				_shift_start_dt="2026-07-30 08:00:00", _shift_end_dt="2026-07-30 16:00:00",
				payment_method="Cash", opening_amount=100, expected_amount=150, closing_amount=150,
			),
			frappe._dict(
				shift="SHIFT-2", pos_profile="Profile A", cashier="b@example.com",
				posting_date="2026-07-31", shift_start="08:00", shift_end="16:00",
				_shift_start_dt="2026-07-31 08:00:00", _shift_end_dt="2026-07-31 16:00:00",
				payment_method="نقد", opening_amount=0, expected_amount=200, closing_amount=198,
			),
		]
		sql.return_value = raw
		transaction_counts.return_value = {"SHIFT-1": 2, "SHIFT-2": 3}
		deposits.return_value = {
			"SHIFT-1": {"deposit_amount": 125.5, "deposit_date": "2026-07-30"}
		}
		data, methods = payments_and_cash_control_report.get_data(
			{"from_date": "2026-07-30", "to_date": "2026-07-31", "pos_profile": "Profile A"}
		)
		rows = {row["shift"]: row for row in data}
		self.assertEqual(rows["SHIFT-1"]["bank_deposit_amount"], 125.5)
		self.assertEqual(rows["SHIFT-1"]["deposit_date"], "2026-07-30")
		self.assertEqual(rows["SHIFT-2"]["bank_deposit_amount"], 0)
		self.assertIsNone(rows["SHIFT-2"]["deposit_date"])
		self.assertEqual(methods, ["Cash", "نقد"])
		transaction_counts.assert_called_once_with(raw)
		deposits.assert_called_once_with(raw)
		sql.assert_called_once()

	def test_payment_method_fieldnames_are_ascii_stable_and_unique(self):
		methods = ["Cash", "cash", "Card / Visa", "Card-Visa", "نقد", "💳"]
		first = payment_method_fieldnames(methods)
		second = payment_method_fieldnames(reversed(methods))
		self.assertEqual(first, second)
		self.assertEqual(len(set(first.values())), len(methods))
		for fieldname in first.values():
			self.assertRegex(fieldname, re.compile(r"^[a-z0-9_]+$"))
