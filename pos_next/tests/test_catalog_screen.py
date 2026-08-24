# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

"""Unit tests for the classic item-management screen endpoints (catalog.py).

Mock-based (no DB writes), matching the app's test convention: the whitelisted APIs are
exercised at their logic boundary with the DB / permission / reconciliation layers patched.
End-to-end item + stock + price behaviour is verified separately against the live schema.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

import frappe

from pos_next.api import catalog


def _throw(msg, exc=None, **kwargs):
	raise (exc or frappe.ValidationError)(msg)


class TestApplyStockAndPrices(TestCase):
	"""qty writes stock via reconciliation when it changes; otherwise prices are upserted."""

	def test_rejects_negative_qty(self):
		with patch.object(catalog.frappe, "throw", side_effect=_throw), self.assertRaises(frappe.ValidationError):
			catalog._apply_stock_and_prices("P", "C", "IT", "Nos", qty=-1, cost=0, selling=0, current_qty=0)

	def test_positive_qty_requires_cost(self):
		with patch.object(catalog.frappe, "throw", side_effect=_throw), self.assertRaises(frappe.ValidationError):
			catalog._apply_stock_and_prices("P", "C", "IT", "Nos", qty=5, cost=0, selling=10, current_qty=0)

	def test_reconciles_when_qty_changes(self):
		with patch("pos_next.api.inventory.submit_pos_stock_reconciliation") as recon:
			catalog._apply_stock_and_prices("P", "C", "IT", "Nos", qty=5, cost=10, selling=15, current_qty=0)
		recon.assert_called_once()
		row = recon.call_args.kwargs["rows"][0]
		self.assertEqual((row["qty"], row["buying_rate"], row["selling_rate"]), (5, 10, 15))

	def test_upserts_prices_without_reconciling_when_qty_unchanged(self):
		with (
			patch.object(catalog, "_catalog_price_lists", return_value=(frappe._dict(name="SELL"), frappe._dict(name="BUY"))),
			patch.object(catalog, "_upsert_item_price") as upsert,
			patch("pos_next.api.inventory.submit_pos_stock_reconciliation") as recon,
		):
			catalog._apply_stock_and_prices("P", "C", "IT", "Nos", qty=5, cost=10, selling=15, current_qty=5)
		recon.assert_not_called()
		self.assertEqual(upsert.call_count, 2)  # cost + selling


class TestCreateCatalogItem(TestCase):
	def test_item_name_required(self):
		with (
			patch.object(catalog, "_context", return_value=("P", "C")),
			patch.object(catalog.frappe, "has_permission", return_value=True),
			patch.object(catalog.frappe, "throw", side_effect=_throw),
			self.assertRaises(frappe.ValidationError),
		):
			catalog.create_catalog_item(item_name="   ", item_group="G", pos_profile="P")

	def test_cannot_bypass_disabled_catalog_flag(self):
		with (
			patch.object(catalog, "_context", side_effect=frappe.PermissionError),
			patch.object(catalog.frappe, "has_permission") as permission,
			self.assertRaises(frappe.PermissionError),
		):
			catalog.create_catalog_item(item_name="X", item_group="G", pos_profile="P")
		permission.assert_not_called()


class TestNextItemCode(TestCase):
	def test_uses_pos_series_and_avoids_collisions(self):
		with (
			patch("frappe.model.naming.make_autoname", side_effect=["POS-ITM-00001", "POS-ITM-00002"]),
			patch.object(catalog.frappe.db, "exists", side_effect=[True, False]),  # first taken, second free
		):
			self.assertEqual(catalog._next_item_code(), "POS-ITM-00002")


class TestDeleteCatalogItem(TestCase):
	@staticmethod
	def _item():
		item = MagicMock()
		item.name = "IT-1"
		item.disabled = 0
		return item

	def test_soft_deletes_item_with_stock_history(self):
		item = self._item()
		database = MagicMock()
		database.exists.return_value = "SLE-1"  # has stock ledger history
		with (
			patch.object(catalog, "_context", return_value=("P", "C")),
			patch.object(catalog, "assert_doc_permission", return_value=item),
			patch.dict(catalog.frappe.__dict__, {"db": database}),
			patch.object(catalog.frappe, "delete_doc") as delete_doc,
		):
			result = catalog.delete_catalog_item("IT-1", pos_profile="P")
		delete_doc.assert_not_called()
		item.save.assert_called_once()
		self.assertTrue(result["disabled"])
		self.assertFalse(result["deleted"])

	def test_hard_deletes_when_no_history_and_delete_permission(self):
		item = self._item()
		database = MagicMock()
		database.exists.return_value = None  # no history
		with (
			patch.object(catalog, "_context", return_value=("P", "C")),
			patch.object(catalog, "assert_doc_permission", return_value=item),
			patch.dict(catalog.frappe.__dict__, {"db": database}),
			patch.object(catalog.frappe, "has_permission", return_value=True),
			patch.object(catalog.frappe, "delete_doc") as delete_doc,
		):
			result = catalog.delete_catalog_item("IT-1", pos_profile="P")
		delete_doc.assert_called_once()
		self.assertTrue(result["deleted"])

	def test_soft_deletes_when_no_delete_permission(self):
		item = self._item()
		database = MagicMock()
		database.exists.return_value = None
		with (
			patch.object(catalog, "_context", return_value=("P", "C")),
			patch.object(catalog, "assert_doc_permission", return_value=item),
			patch.dict(catalog.frappe.__dict__, {"db": database}),
			patch.object(catalog.frappe, "has_permission", return_value=False),  # no Item delete
			patch.object(catalog.frappe, "delete_doc") as delete_doc,
		):
			result = catalog.delete_catalog_item("IT-1", pos_profile="P")
		delete_doc.assert_not_called()
		item.save.assert_called_once()
		self.assertTrue(result["disabled"])


class TestCatalogScreenGating(TestCase):
	"""Every screen endpoint refuses when the catalog feature/permission is off."""

	def _assert_gated(self, call):
		with (
			patch.object(catalog, "_context", side_effect=frappe.PermissionError),
			self.assertRaises(frappe.PermissionError),
		):
			call()

	def test_list_gated(self):
		self._assert_gated(lambda: catalog.get_catalog_items(pos_profile="P"))

	def test_get_gated(self):
		self._assert_gated(lambda: catalog.get_catalog_item(item_code="X", pos_profile="P"))

	def test_update_gated(self):
		self._assert_gated(lambda: catalog.update_catalog_item(item_code="X", pos_profile="P"))

	def test_delete_gated(self):
		self._assert_gated(lambda: catalog.delete_catalog_item(item_code="X", pos_profile="P"))
