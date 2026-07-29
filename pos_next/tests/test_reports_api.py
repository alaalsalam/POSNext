# Copyright (c) 2025, POS Next and contributors
# For license information, please see license.txt

import unittest
import frappe
from frappe.tests.utils import FrappeTestCase
from pos_next.api import reports


class TestReportsAPI(FrappeTestCase):
    """Tests for pos_next.api.reports — ensure permission gates, date resolution,
    and aggregation logic are correct."""

    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")

    def tearDown(self):
        frappe.set_user("Administrator")

    # ── _date_range ──────────────────────────────────────────────────────────
    def test_date_range_today(self):
        fd, td = reports._date_range("today")
        self.assertEqual(fd, td)
        from frappe.utils import nowdate
        self.assertEqual(fd, nowdate())

    def test_date_range_yesterday(self):
        from frappe.utils import nowdate, add_days
        fd, td = reports._date_range("yesterday")
        self.assertEqual(fd, td)
        self.assertEqual(fd, add_days(nowdate(), -1))

    def test_date_range_custom(self):
        fd, td = reports._date_range("custom", from_date="2025-01-01", to_date="2025-01-31")
        self.assertEqual(fd, "2025-01-01")
        self.assertEqual(td, "2025-01-31")

    def test_date_range_fallback(self):
        """Unknown period falls back to today."""
        from frappe.utils import nowdate
        fd, td = reports._date_range("unknown_period")
        self.assertEqual(fd, nowdate())

    # ── _get_user_pos_profiles ───────────────────────────────────────────────
    def test_get_user_pos_profiles_returns_list(self):
        """Should return a list (possibly empty) without throwing."""
        result = reports._get_user_pos_profiles("Administrator")
        self.assertIsInstance(result, list)

    # ── _assert_profile_access ───────────────────────────────────────────────
    def test_assert_profile_access_denies_unauthorized(self):
        """A user who does not own a profile should be denied."""
        frappe.set_user("Guest")
        with self.assertRaises(frappe.PermissionError):
            reports._assert_profile_access("NonExistentProfile")
        frappe.set_user("Administrator")

    # ── get_report_filters ───────────────────────────────────────────────────
    def test_get_report_filters_structure(self):
        frappe.set_user("Administrator")
        result = reports.get_report_filters()
        self.assertIn("pos_profiles", result)
        self.assertIn("periods", result)
        self.assertIsInstance(result["pos_profiles"], list)
        self.assertIsInstance(result["periods"], list)
        self.assertTrue(len(result["periods"]) >= 4)

    # ── get_daily_summary ────────────────────────────────────────────────────
    def test_get_daily_summary_no_data(self):
        """If there are no invoices for a profile, summary should be zeros."""
        # Use a fake POS profile that the current user can access
        # We mock _assert_profile_access and _get_invoice_names
        original_assert = reports._assert_profile_access
        original_invoices = reports._get_invoice_names
        try:
            reports._assert_profile_access = lambda p: None
            reports._get_invoice_names = lambda *a, **kw: []
            # Also mock currency lookup
            import frappe.utils
            orig_get = frappe.db.get_value
            frappe.db.get_value = lambda dt, n, f, **kw: "SAR" if f == "currency" else orig_get(dt, n, f, **kw)

            result = reports.get_daily_summary("FakeProfile", period="today")
            self.assertEqual(result["sales_total"], 0.0)
            self.assertEqual(result["sales_count"], 0)
            self.assertEqual(result["returns_total"], 0.0)
            self.assertEqual(result["net_sales"], 0.0)
        finally:
            reports._assert_profile_access = original_assert
            reports._get_invoice_names = original_invoices
            frappe.db.get_value = orig_get

    def test_get_daily_summary_aggregation(self):
        """Verify sales/returns aggregation logic with mock invoice data."""
        original_assert = reports._assert_profile_access
        original_invoices = reports._get_invoice_names
        orig_get = frappe.db.get_value
        try:
            reports._assert_profile_access = lambda p: None
            reports._get_invoice_names = lambda *a, **kw: [
                frappe._dict(is_return=0, grand_total=500, outstanding_amount=0),
                frappe._dict(is_return=0, grand_total=300, outstanding_amount=100),
                frappe._dict(is_return=1, grand_total=-50, outstanding_amount=0),
            ]
            frappe.db.get_value = lambda dt, n, f, **kw: "SAR"

            result = reports.get_daily_summary("FakeProfile", period="today")
            self.assertEqual(result["sales_count"], 2)
            self.assertEqual(result["sales_total"], 800.0)
            self.assertEqual(result["returns_count"], 1)
            self.assertEqual(result["returns_total"], 50.0)
            self.assertAlmostEqual(result["net_sales"], 750.0)
            self.assertAlmostEqual(result["avg_invoice"], 400.0)
            self.assertEqual(result["outstanding_total"], 100.0)
        finally:
            reports._assert_profile_access = original_assert
            reports._get_invoice_names = original_invoices
            frappe.db.get_value = orig_get

    # ── get_payment_breakdown ────────────────────────────────────────────────
    def test_get_payment_breakdown_empty(self):
        """Empty invoice list returns empty methods."""
        original_assert = reports._assert_profile_access
        original_invoices = reports._get_invoice_names
        try:
            reports._assert_profile_access = lambda p: None
            reports._get_invoice_names = lambda *a, **kw: []

            result = reports.get_payment_breakdown("FakeProfile", period="today")
            self.assertEqual(result["methods"], [])
            self.assertEqual(result["grand_total"], 0.0)
        finally:
            reports._assert_profile_access = original_assert
            reports._get_invoice_names = original_invoices

    def test_get_payment_breakdown_percentages(self):
        """Verify percentage calculations are correct."""
        original_assert = reports._assert_profile_access
        original_invoices = reports._get_invoice_names
        orig_get_all = frappe.get_all
        try:
            reports._assert_profile_access = lambda p: None
            reports._get_invoice_names = lambda *a, **kw: [
                frappe._dict(name="SI-001", grand_total=600, is_return=0, outstanding_amount=0,
                             net_total=600, total_taxes_and_charges=0, posting_datetime=None,
                             posting_date=None, customer=None, currency="SAR"),
                frappe._dict(name="SI-002", grand_total=400, is_return=0, outstanding_amount=0,
                             net_total=400, total_taxes_and_charges=0, posting_datetime=None,
                             posting_date=None, customer=None, currency="SAR"),
            ]
            # Mock payment rows
            frappe.get_all = lambda dt, **kw: (
                [frappe._dict(parent="SI-001", mode_of_payment="Cash", amount=600),
                 frappe._dict(parent="SI-002", mode_of_payment="Card", amount=400)]
                if dt == "Sales Invoice Payment" else orig_get_all(dt, **kw)
            )

            result = reports.get_payment_breakdown("FakeProfile", period="today")
            methods = {m["mode"]: m for m in result["methods"]}
            self.assertAlmostEqual(methods["Cash"]["percentage"], 60.0)
            self.assertAlmostEqual(methods["Card"]["percentage"], 40.0)
            self.assertEqual(result["grand_total"], 1000.0)
        finally:
            reports._assert_profile_access = original_assert
            reports._get_invoice_names = original_invoices
            frappe.get_all = orig_get_all

    # ── get_current_shift_profile ────────────────────────────────────────────
    def test_get_current_shift_profile_no_shift(self):
        """When no open shift exists, should return None."""
        orig_get_all = frappe.get_all
        try:
            frappe.get_all = lambda dt, **kw: [] if dt == "POS Opening Shift" else orig_get_all(dt, **kw)
            result = reports.get_current_shift_profile()
            self.assertIsNone(result["pos_profile"])
        finally:
            frappe.get_all = orig_get_all


if __name__ == "__main__":
    unittest.main()
