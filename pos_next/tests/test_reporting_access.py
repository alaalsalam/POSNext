# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

import importlib
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from pos_next.api import reporting_access


class TestReportingAccess(FrappeTestCase):
	def test_all_five_desk_reports_reject_before_query(self):
		modules = [
			"pos_next.pos_next.report.sales_vs_shifts_report.sales_vs_shifts_report",
			"pos_next.pos_next.report.cashier_performance_report.cashier_performance_report",
			"pos_next.pos_next.report.payments_and_cash_control_report.payments_and_cash_control_report",
			"pos_next.pos_next.report.inventory_impact_and_fast_movers_report.inventory_impact_and_fast_movers_report",
			"pos_next.pos_next.report.offline_sync_and_system_health_report.offline_sync_and_system_health_report",
		]
		for module_path in modules:
			with self.subTest(module=module_path):
				module = importlib.import_module(module_path)
				with patch.object(module, "authorize_report", side_effect=frappe.PermissionError):
					with self.assertRaises(frappe.PermissionError):
						module.execute({"pos_profile": "Profile A"})

	@patch.object(reporting_access.frappe, "has_permission", return_value=True)
	@patch.object(reporting_access.frappe, "get_roles", return_value=["POSNext Cashier"])
	def test_cashier_cannot_open_reports_even_with_doctype_read(self, _roles, _permission):
		with self.assertRaises(frappe.PermissionError):
			reporting_access.assert_report_manager()

	@patch.object(reporting_access, "assert_report_manager")
	def test_profile_is_mandatory(self, _manager):
		with self.assertRaises(frappe.PermissionError):
			reporting_access.authorize_report({})

	@patch.object(reporting_access, "require_feature")
	@patch.object(reporting_access, "assert_report_manager")
	def test_direct_report_request_is_flag_guarded(self, _manager, require_feature):
		reporting_access.authorize_report({"pos_profile": "Profile A"})
		require_feature.assert_called_once_with("pos_reports", pos_profile="Profile A")

	@patch.object(reporting_access, "get_feature_flags")
	@patch.object(reporting_access.frappe, "get_all")
	@patch.object(reporting_access, "assert_report_manager")
	def test_profile_and_company_denial_excludes_foreign_profile(self, _manager, get_all, flags):
		frappe.set_user("manager@example.com")
		self.addCleanup(frappe.set_user, "Administrator")
		get_all.side_effect = [
			["Profile A", "Profile B"],
			[
				frappe._dict(name="Profile A", company="Company A", currency="SAR"),
				frappe._dict(name="Profile B", company="Company B", currency="SAR"),
			],
		]

		def feature_flags(pos_profile):
			if pos_profile == "Profile B":
				raise frappe.PermissionError
			return {"enable_pos_reports": 1}

		flags.side_effect = feature_flags
		result = reporting_access.get_reportable_profiles()
		self.assertEqual([row.name for row in result], ["Profile A"])
