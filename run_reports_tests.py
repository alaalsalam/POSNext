"""Standalone runner for pos_next reports API tests."""
import sys
import unittest
import frappe

def run():
    import os
    os.chdir("/home/erpnext/frappe-bench16")
    frappe.init(site="digitpos.trilogy-erp.com", sites_path="/home/erpnext/frappe-bench16/sites")
    frappe.connect()
    frappe.set_user("Administrator")

    # Import after frappe context is up
    from pos_next.api import reports

    passed = 0
    failed = 0
    errors = []

    from frappe.utils import nowdate, add_days

    # ── _date_range tests ────────────────────────────────────────────────────
    def test_date_range_today():
        fd, td = reports._date_range("today")
        assert fd == td, f"Expected fd==td, got {fd} != {td}"
        assert fd == nowdate(), f"Expected today {nowdate()}, got {fd}"

    def test_date_range_yesterday():
        fd, td = reports._date_range("yesterday")
        assert fd == td
        assert fd == add_days(nowdate(), -1)

    def test_date_range_custom():
        fd, td = reports._date_range("custom", from_date="2025-01-01", to_date="2025-01-31")
        assert fd == "2025-01-01"
        assert td == "2025-01-31"

    def test_date_range_fallback():
        fd, td = reports._date_range("unknown_period")
        assert fd == nowdate(), f"Fallback should be today, got {fd}"

    # ── _get_user_pos_profiles ───────────────────────────────────────────────
    def test_get_user_pos_profiles_returns_list():
        result = reports._get_user_pos_profiles("Administrator")
        assert isinstance(result, list)

    # ── _assert_profile_access ───────────────────────────────────────────────
    def test_assert_profile_access_denies_unauthorized():
        frappe.set_user("Guest")
        try:
            raised = False
            try:
                reports._assert_profile_access("NonExistentProfile")
            except frappe.PermissionError:
                raised = True
            assert raised, "Expected PermissionError for Guest user"
        finally:
            frappe.set_user("Administrator")

    # ── get_report_filters ───────────────────────────────────────────────────
    def test_get_report_filters_structure():
        result = reports.get_report_filters()
        assert "pos_profiles" in result
        assert "periods" in result
        assert isinstance(result["pos_profiles"], list)
        assert isinstance(result["periods"], list)
        assert len(result["periods"]) >= 4

    # ── get_daily_summary no data ────────────────────────────────────────────
    def test_get_daily_summary_no_data():
        original_assert = reports._assert_profile_access
        original_invoices = reports._get_invoice_names
        orig_get = frappe.db.get_value
        try:
            reports._assert_profile_access = lambda p: None
            reports._get_invoice_names = lambda *a, **kw: []
            frappe.db.get_value = lambda dt, n, f, **kw: "SAR" if f == "currency" else orig_get(dt, n, f, **kw)

            result = reports.get_daily_summary("FakeProfile", period="today")
            assert result["sales_total"] == 0.0, f"sales_total={result['sales_total']}"
            assert result["sales_count"] == 0
            assert result["returns_total"] == 0.0
            assert result["net_sales"] == 0.0
        finally:
            reports._assert_profile_access = original_assert
            reports._get_invoice_names = original_invoices
            frappe.db.get_value = orig_get

    # ── get_daily_summary aggregation ────────────────────────────────────────
    def test_get_daily_summary_aggregation():
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
            assert result["sales_count"] == 2, f"sales_count={result['sales_count']}"
            assert result["sales_total"] == 800.0, f"sales_total={result['sales_total']}"
            assert result["returns_count"] == 1
            assert result["returns_total"] == 50.0
            assert abs(result["net_sales"] - 750.0) < 0.01
            assert abs(result["avg_invoice"] - 400.0) < 0.01
            assert result["outstanding_total"] == 100.0
        finally:
            reports._assert_profile_access = original_assert
            reports._get_invoice_names = original_invoices
            frappe.db.get_value = orig_get

    # ── get_payment_breakdown empty ──────────────────────────────────────────
    def test_get_payment_breakdown_empty():
        original_assert = reports._assert_profile_access
        original_invoices = reports._get_invoice_names
        try:
            reports._assert_profile_access = lambda p: None
            reports._get_invoice_names = lambda *a, **kw: []

            result = reports.get_payment_breakdown("FakeProfile", period="today")
            assert result["methods"] == []
            assert result["grand_total"] == 0.0
        finally:
            reports._assert_profile_access = original_assert
            reports._get_invoice_names = original_invoices

    # ── get_payment_breakdown percentages ────────────────────────────────────
    def test_get_payment_breakdown_percentages():
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
            frappe.get_all = lambda dt, **kw: (
                [frappe._dict(parent="SI-001", mode_of_payment="Cash", amount=600),
                 frappe._dict(parent="SI-002", mode_of_payment="Card", amount=400)]
                if dt == "Sales Invoice Payment" else orig_get_all(dt, **kw)
            )

            result = reports.get_payment_breakdown("FakeProfile", period="today")
            methods = {m["mode"]: m for m in result["methods"]}
            assert abs(methods["Cash"]["percentage"] - 60.0) < 0.1, f"Cash%={methods['Cash']['percentage']}"
            assert abs(methods["Card"]["percentage"] - 40.0) < 0.1, f"Card%={methods['Card']['percentage']}"
            assert result["grand_total"] == 1000.0
        finally:
            reports._assert_profile_access = original_assert
            reports._get_invoice_names = original_invoices
            frappe.get_all = orig_get_all

    # ── get_current_shift_profile no shift ───────────────────────────────────
    def test_get_current_shift_profile_no_shift():
        orig_get_all = frappe.get_all
        try:
            frappe.get_all = lambda dt, **kw: [] if dt == "POS Opening Shift" else orig_get_all(dt, **kw)
            result = reports.get_current_shift_profile()
            assert result["pos_profile"] is None, f"Expected None, got {result['pos_profile']}"
        finally:
            frappe.get_all = orig_get_all

    tests = [
        test_date_range_today,
        test_date_range_yesterday,
        test_date_range_custom,
        test_date_range_fallback,
        test_get_user_pos_profiles_returns_list,
        test_assert_profile_access_denies_unauthorized,
        test_get_report_filters_structure,
        test_get_daily_summary_no_data,
        test_get_daily_summary_aggregation,
        test_get_payment_breakdown_empty,
        test_get_payment_breakdown_percentages,
        test_get_current_shift_profile_no_shift,
    ]

    for t in tests:
        name = t.__name__
        try:
            t()
            print(f"PASSED  {name}")
            passed += 1
        except Exception as e:
            print(f"FAILED  {name}: {e}")
            failed += 1
            errors.append((name, str(e)))

    print(f"\n{'='*60}")
    print(f"Ran {passed + failed} tests — {passed} passed, {failed} failed")
    if errors:
        print("\nFailures:")
        for name, msg in errors:
            print(f"  {name}: {msg}")

    frappe.destroy()
    return failed

if __name__ == "__main__":
    sys.exit(run())
