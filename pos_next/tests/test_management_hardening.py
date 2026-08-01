from unittest import TestCase
from unittest.mock import MagicMock, patch

import frappe

from pos_next.api import catalog, permissions, purchases
from pos_next.api.management_scope import normalize_idempotency_key, require_manager_feature


class TestManagementScope(TestCase):
	def test_cashier_permission_bootstrap_hides_all_manager_workflows(self):
		flags = {
			"enable_catalog_management": 1,
			"enable_purchases": 1,
			"enable_supplier_payments": 1,
			"enable_pos_reports": 0,
		}
		with (
			patch.object(permissions, "get_feature_flags", return_value=flags),
			patch.object(permissions, "is_feature_manager", return_value=False),
			patch.object(permissions.frappe, "get_roles", return_value=["POSNext Cashier"]),
			patch.object(permissions.frappe, "has_permission", return_value=True),
		):
			result = permissions.get_pos_permissions("POS-A")
		for field in (
			"can_create_items", "can_write_items", "can_read_purchases", "can_create_purchases",
			"can_write_purchases", "can_submit_purchases", "can_cancel_purchases",
			"can_read_payment_entries", "can_create_payment_entries", "can_write_payment_entries",
			"can_submit_payment_entries", "can_cancel_payment_entries",
		):
			self.assertFalse(result[field], field)

	def test_cashier_cannot_bypass_any_catalog_endpoint(self):
		calls = (
			lambda: catalog.check_catalog_permission("POS-A"),
			lambda: catalog.get_catalog_defaults("POS-A"),
			lambda: catalog.get_item_groups_for_select("POS-A"),
			lambda: catalog.create_item_group("Group", pos_profile="POS-A"),
			lambda: catalog.create_quick_item("Item", "Group", pos_profile="POS-A"),
			lambda: catalog.get_item_prices("ITEM", "POS-A"),
			lambda: catalog.update_item_prices("ITEM", selling_price=1, pos_profile="POS-A"),
		)
		for invoke in calls:
			with self.subTest(endpoint=invoke), patch.object(catalog, "_context", side_effect=frappe.PermissionError):
				with self.assertRaises(frappe.PermissionError):
					invoke()

	def test_cashier_cannot_bypass_any_purchase_or_payment_endpoint(self):
		calls = (
			lambda: purchases.get_suppliers(pos_profile="POS-A"),
			lambda: purchases.get_supplier_groups("POS-A"),
			lambda: purchases.create_supplier("Supplier", "Group", pos_profile="POS-A"),
			lambda: purchases.get_purchase_invoices(pos_profile="POS-A"),
			lambda: purchases.get_purchase_invoice("PINV", "POS-A"),
			lambda: purchases.get_new_purchase_invoice_defaults("POS-A"),
			lambda: purchases.get_purchase_currencies("POS-A"),
			lambda: purchases.save_purchase_invoice({}, pos_profile="POS-A"),
			lambda: purchases.submit_purchase_invoice("PINV", "modified", "POS-A"),
			lambda: purchases.cancel_purchase_invoice("PINV", "POS-A"),
			lambda: purchases.get_purchase_items(pos_profile="POS-A"),
			lambda: purchases.get_item_buying_price("ITEM", pos_profile="POS-A"),
			lambda: purchases.get_warehouses("POS-A"),
			lambda: purchases.get_expense_accounts("POS-A"),
			lambda: purchases.get_purchase_tax_templates("POS-A"),
			lambda: purchases.get_supplier_payment_defaults("PINV", "POS-A"),
			lambda: purchases.create_supplier_payment("PINV", 1, "Cash", "payment-key", pos_profile="POS-A"),
			lambda: purchases.submit_supplier_payment("PAY", "modified", "POS-A"),
			lambda: purchases.cancel_supplier_payment("PAY", "POS-A"),
			lambda: purchases.get_supplier_payments(pos_profile="POS-A"),
			lambda: purchases.get_purchase_outstanding_summary(pos_profile="POS-A"),
		)
		for invoke in calls:
			with self.subTest(endpoint=invoke), patch.object(purchases, "_context", side_effect=frappe.PermissionError):
				with self.assertRaises(frappe.PermissionError):
					invoke()

	def test_cashier_is_denied_after_flag_check(self):
		with (
			patch("pos_next.api.management_scope.require_feature", return_value="POS-A"),
			patch("pos_next.api.management_scope.is_feature_manager", return_value=False),
			self.assertRaises(frappe.PermissionError),
		):
			require_manager_feature("purchases", "POS-A")

	def test_company_mismatch_is_passed_to_feature_guard(self):
		with patch("pos_next.api.management_scope.require_feature", side_effect=frappe.PermissionError) as guard:
			with self.assertRaises(frappe.PermissionError):
				require_manager_feature("purchases", "POS-A", "Foreign Company")
		guard.assert_called_once_with("purchases", pos_profile="POS-A", company="Foreign Company")

	def test_idempotency_key_format(self):
		self.assertEqual(normalize_idempotency_key("purchase-1234"), "purchase-1234")
		for value in ("", "short", "bad key with spaces", "../unsafe?"):
			with self.assertRaises(frappe.ValidationError):
				normalize_idempotency_key(value)


class TestCatalogHardening(TestCase):
	def test_opening_stock_placeholder_is_closed(self):
		with (
			patch.object(catalog, "_context", return_value=("POS-A", "Company A")),
			patch.object(catalog.frappe, "has_permission", return_value=True),
			self.assertRaises(frappe.ValidationError),
		):
			catalog.create_quick_item("Item", "Group", opening_qty=1, pos_profile="POS-A")

	def test_foreign_price_list_is_rejected(self):
		item = frappe._dict(name="ITEM-1", stock_uom="Nos")
		with (
			patch.object(catalog, "_context", return_value=("POS-A", "Company A")),
			patch.object(catalog, "assert_doc_permission", return_value=item),
			patch.object(catalog, "_assert_uom"),
			patch.object(catalog, "_catalog_price_lists", return_value=(frappe._dict(name="Selling A"), frappe._dict(name="Buying A"))),
			patch.object(catalog.frappe, "has_permission", return_value=True),
			self.assertRaises(frappe.PermissionError),
		):
			catalog.update_item_prices("ITEM-1", selling_price=10, selling_price_list="Selling B", pos_profile="POS-A")

	def test_item_price_update_is_idempotent(self):
		price = frappe._dict(name="IP-1", price_list="Selling A", price_list_rate=10, uom="Nos")
		price.save = MagicMock()
		price_list = frappe._dict(name="Selling A")
		with (
			patch.object(catalog.frappe, "get_list", return_value=["IP-1"]),
			patch.object(catalog, "assert_doc_permission", return_value=price),
		):
			result = catalog._upsert_item_price("ITEM-1", price_list, 12, "Nos")
		price.save.assert_called_once_with(ignore_permissions=False)
		self.assertEqual(result["name"], "IP-1")


class TestPurchaseHardening(TestCase):
	def test_purchase_retry_key_cannot_change_items(self):
		doc = frappe._dict(
			supplier="SUP",
			bill_no="BILL-1",
			currency="SAR",
			buying_price_list="Buying",
			update_stock=0,
			items=[frappe._dict(item_code="ITEM-1", qty=1, rate=10, warehouse=None)],
		)
		with self.assertRaises(frappe.PermissionError):
			purchases._assert_purchase_replay_matches(
				doc,
				{"supplier": "SUP", "bill_no": "BILL-1", "items": [{"item_code": "ITEM-2", "qty": 1, "rate": 10}]},
			)

	def test_foreign_company_resource_is_rejected(self):
		with patch("pos_next.api.management_scope.assert_doc_permission", return_value=frappe._dict(company="Company B", is_group=0, disabled=0)):
			with self.assertRaises(frappe.PermissionError):
				purchases.assert_company_resource("Warehouse", "Foreign Warehouse", "Company A")

	def test_payment_history_loads_allocations_in_one_batch(self):
		payments = [
			frappe._dict(name="PAY-1"),
			frappe._dict(name="PAY-2"),
		]
		allocation = frappe._dict(
			parent="PAY-2",
			reference_name="PINV-1",
			allocated_amount=25,
			outstanding_amount=50,
		)
		with (
			patch.object(purchases, "_context", return_value=("POS-A", "Company A")),
			patch.object(purchases.frappe, "has_permission", return_value=True),
			patch.object(
				purchases.frappe,
				"get_list",
				side_effect=[payments, ["PAY-1", "PAY-2"]],
			),
			patch.object(purchases.frappe, "get_all", return_value=[allocation]) as get_all,
		):
			result = purchases.get_supplier_payments(pos_profile="POS-A")
		self.assertEqual(result["payments"][0].allocations, [])
		self.assertEqual(result["payments"][1].allocations, [allocation])
		get_all.assert_called_once()

	def test_supplier_user_permission_denial_propagates(self):
		with patch.object(purchases, "assert_doc_permission", side_effect=frappe.PermissionError):
			with self.assertRaises(frappe.PermissionError):
				purchases._assert_supplier("FOREIGN-SUPPLIER")

	def test_mass_assignment_is_rejected(self):
		with (
			patch.object(purchases, "_assert_supplier"),
			patch.object(purchases, "_default_buying_price_list", return_value="Buying"),
			patch.object(purchases, "_assert_price_list"),
			patch.object(purchases, "_validate_currency"),
			self.assertRaises(frappe.ValidationError),
		):
			purchases._validate_purchase_payload({"supplier": "SUP", "items": [], "owner": "Administrator"}, "POS-A", "Company A")

	def test_stale_purchase_draft_is_rejected(self):
		doc = frappe._dict(name="PINV-1", docstatus=0, company="Company A", custom_posnext_pos_profile="POS-A")
		with (
			patch.object(purchases, "_context", return_value=("POS-A", "Company A")),
			patch.object(purchases, "lock_document", return_value=frappe._dict(modified="newer", docstatus=0)),
			patch.object(purchases, "_get_purchase_invoice", return_value=doc),
			patch.object(purchases.frappe, "has_permission", return_value=True),
			self.assertRaises(frappe.TimestampMismatchError),
		):
			purchases.save_purchase_invoice({"name": "PINV-1", "company": "Company A"}, expected_modified="older", pos_profile="POS-A")
