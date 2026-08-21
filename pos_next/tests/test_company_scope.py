from unittest import TestCase
from unittest.mock import patch

import frappe

from pos_next.api import company_scope


class FakeDoc:
	def __init__(self, doctype, name, is_new=True, company=None):
		self.doctype = doctype
		self.name = name
		self._new = is_new
		if company is not None:
			setattr(self, company_scope.OWNERSHIP_FIELD, company)

	def is_new(self):
		return self._new

	def get(self, field):
		return getattr(self, field, None)

	def set(self, field, value):
		setattr(self, field, value)


class TestCompanyScope(TestCase):
	def tearDown(self):
		frappe.flags.pop("in_import", None)
		frappe.flags.pop("pos_next_setup_company", None)

	@patch("pos_next.api.company_scope.is_multi_company_site", return_value=True)
	def test_active_company_uses_user_profile_when_default_is_missing(self, _is_multi):
		with (
			patch("pos_next.api.company_scope.frappe.db.has_column", return_value=True),
			patch("pos_next.api.company_scope.frappe.db.get_value") as get_value,
			patch("pos_next.api.company_scope.frappe.db.exists", return_value=True),
			patch("pos_next.api.company_scope.frappe.has_permission", return_value=True),
		):
			get_value.side_effect = lambda doctype, field: {
				("User", company_scope.USER_COMPANY_FIELD): "Company X",
			}.get((doctype, field), None)
			result = company_scope.active_company("test-user")
			self.assertEqual(result, "Company X")

	@patch("pos_next.api.company_scope.is_multi_company_site", return_value=True)
	def test_import_uses_row_company_when_active_company_is_missing(self, _is_multi):
		doc = FakeDoc("Item", "NEW-ITEM", is_new=True, company="Company Y")
		frappe.flags.in_import = True

		with (
			patch("pos_next.api.company_scope.active_company", return_value=None),
			patch("pos_next.api.company_scope.frappe.db.exists", return_value=True),
			patch("pos_next.api.company_scope.frappe.has_permission", return_value=True),
			patch("pos_next.api.company_scope.frappe.db.has_column", return_value=True),
			patch("pos_next.api.company_scope.frappe.db.get_value"),
		):
			company_scope.enforce_company_ownership(doc)
			self.assertEqual(doc.get(company_scope.OWNERSHIP_FIELD), "Company Y")

	def test_import_update_reuses_existing_owned_company(self):
		doc = FakeDoc("Item", "ITEM-1", is_new=False, company="Company Z")
		frappe.flags.in_import = True

		with (
			patch("pos_next.api.company_scope.is_multi_company_site", return_value=True),
			patch("pos_next.api.company_scope.active_company", return_value=None),
			patch("pos_next.api.company_scope.frappe.db.exists", return_value=True),
			patch("pos_next.api.company_scope.frappe.has_permission", return_value=True),
			patch("pos_next.api.company_scope.frappe.db.has_column", return_value=True),
			patch("pos_next.api.company_scope.frappe.db.get_value", return_value="Company Z"),
		):
			company_scope.enforce_company_ownership(doc)
			self.assertEqual(doc.get(company_scope.OWNERSHIP_FIELD), "Company Z")
