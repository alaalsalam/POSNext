# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

from unittest import TestCase
from unittest.mock import MagicMock, patch

import frappe

from pos_next.api import catalog, feature_flags, purchases, reports
from pos_next.api.feature_flags import (
	FEATURE_DEFAULTS,
	assert_profile_access,
	get_feature_flags,
	require_feature,
	validate_feature_dependencies,
)
from pos_next.pos_next.doctype.pos_settings import pos_settings


class TestFeatureFlags(TestCase):
	def test_missing_settings_use_secure_off_defaults(self):
		database = MagicMock()
		database.get_value.return_value = None
		with (
			patch("pos_next.api.feature_flags.resolve_pos_profile", return_value="POS-TEST"),
			patch.dict(feature_flags.frappe.__dict__, {"db": database}),
		):
			self.assertEqual(get_feature_flags("POS-TEST"), FEATURE_DEFAULTS)

	def test_disabled_feature_is_rejected(self):
		with (
			patch("pos_next.api.feature_flags.resolve_pos_profile", return_value="POS-TEST"),
			patch(
				"pos_next.api.feature_flags.get_feature_flags",
				return_value=FEATURE_DEFAULTS.copy(),
			),
			patch.object(feature_flags.frappe, "throw", side_effect=frappe.PermissionError),
			self.assertRaises(frappe.PermissionError),
		):
			require_feature("catalog", pos_profile="POS-TEST")

	def test_enabled_feature_returns_resolved_profile(self):
		flags = FEATURE_DEFAULTS.copy()
		flags["enable_purchases"] = 1
		with (
			patch("pos_next.api.feature_flags.resolve_pos_profile", return_value="POS-TEST"),
			patch("pos_next.api.feature_flags.get_feature_flags", return_value=flags),
		):
			self.assertEqual(require_feature("purchases", pos_profile="POS-TEST"), "POS-TEST")

	def test_supplier_payments_require_purchases(self):
		with (
			patch.object(feature_flags.frappe, "throw", side_effect=frappe.ValidationError),
			self.assertRaises(frappe.ValidationError),
		):
			validate_feature_dependencies(
				frappe._dict(enable_purchases=0, enable_supplier_payments=1)
			)

	def test_catalog_api_cannot_bypass_disabled_flag(self):
		with (
			patch.object(catalog, "require_feature", side_effect=frappe.PermissionError),
			patch.object(catalog.frappe, "has_permission") as permission,
			self.assertRaises(frappe.PermissionError),
		):
			catalog.check_catalog_permission()
		permission.assert_not_called()

	def test_purchase_api_cannot_bypass_disabled_flag(self):
		with (
			patch.object(purchases, "require_feature", side_effect=frappe.PermissionError),
			patch.object(purchases.frappe, "has_permission") as permission,
			self.assertRaises(frappe.PermissionError),
		):
			purchases.get_purchase_invoices()
		permission.assert_not_called()

	def test_supplier_payment_api_cannot_bypass_disabled_flag(self):
		with (
			patch.object(purchases, "require_feature", side_effect=frappe.PermissionError),
			patch.object(purchases.frappe, "has_permission") as permission,
			self.assertRaises(frappe.PermissionError),
		):
			purchases.get_supplier_payments()
		permission.assert_not_called()

	def test_reports_api_cannot_bypass_disabled_flag(self):
		with (
			patch.object(reports, "require_feature", side_effect=frappe.PermissionError),
			patch.object(reports.frappe, "has_permission") as permission,
			self.assertRaises(frappe.PermissionError),
		):
			reports.get_daily_summary("POS-TEST")
		permission.assert_not_called()

	def test_cashier_cannot_mutate_pos_settings_api(self):
		with (
			patch.object(pos_settings, "assert_feature_manager", side_effect=frappe.PermissionError),
			patch.object(pos_settings, "assert_profile_access") as profile_access,
			self.assertRaises(frappe.PermissionError),
		):
			pos_settings.update_pos_settings("POS-A", {"allow_credit_sale": 1})
		profile_access.assert_not_called()

	def test_document_controller_rejects_non_manager_mutation(self):
		doc = MagicMock()
		with (
			patch.object(pos_settings, "assert_feature_manager", side_effect=frappe.PermissionError),
			self.assertRaises(frappe.PermissionError),
		):
			pos_settings.POSSettings.validate(doc)

	def test_authorized_manager_mutation_uses_permission_checked_save(self):
		doc = MagicMock()
		doc.as_dict.return_value = {"name": "POS Settings A"}
		database = MagicMock()
		database.exists.return_value = "POS Settings A"
		meta = MagicMock()
		meta.get_field.return_value = frappe._dict(read_only=0, fieldtype="Check")
		with (
			patch.object(pos_settings, "assert_feature_manager"),
			patch.object(pos_settings, "assert_profile_access"),
			patch.object(pos_settings.frappe, "has_permission", return_value=True),
			patch.object(pos_settings.frappe, "get_doc", return_value=doc),
			patch.object(pos_settings.frappe, "get_meta", return_value=meta),
			patch.dict(pos_settings.frappe.__dict__, {"db": database}),
		):
			result = pos_settings.update_pos_settings("POS-A", {"allow_credit_sale": 1})
		doc.update.assert_called_once_with({"allow_credit_sale": 1})
		doc.save.assert_called_once_with()
		self.assertEqual(result["name"], "POS Settings A")

	def test_settings_api_rejects_profile_relinking(self):
		with (
			patch.object(pos_settings, "assert_feature_manager"),
			patch.object(pos_settings, "assert_profile_access"),
			patch.object(pos_settings.frappe, "has_permission", return_value=True),
			patch.object(pos_settings.frappe, "throw", side_effect=frappe.PermissionError),
			self.assertRaises(frappe.PermissionError),
		):
			pos_settings.update_pos_settings("POS-A", {"pos_profile": "POS-B"})

	def test_user_assigned_to_profile_a_cannot_read_profile_b_flags(self):
		database = MagicMock()
		database.exists.return_value = False
		session = frappe._dict(user="cashier@example.com")
		with (
			patch.dict(feature_flags.frappe.__dict__, {"db": database, "session": session}),
			patch.object(feature_flags.frappe, "throw", side_effect=frappe.PermissionError),
			self.assertRaises(frappe.PermissionError),
		):
			assert_profile_access("POS-B")
		database.exists.assert_called_once_with(
			"POS Profile User", {"parent": "POS-B", "user": "cashier@example.com"}
		)

	def test_manager_cannot_bypass_company_user_permission(self):
		database = MagicMock()
		database.exists.return_value = True
		database.get_value.return_value = "Company B"
		session = frappe._dict(user="manager@example.com")

		def has_permission(doctype, ptype, **kwargs):
			return doctype == "POS Profile"

		with (
			patch.dict(feature_flags.frappe.__dict__, {"db": database, "session": session}),
			patch.object(feature_flags.frappe, "has_permission", side_effect=has_permission),
			patch.object(feature_flags.frappe, "throw", side_effect=frappe.PermissionError),
			self.assertRaises(frappe.PermissionError),
		):
			assert_profile_access("POS-B")
