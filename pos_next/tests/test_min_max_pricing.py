"""Focused regression tests for Min/Max pricing rule post-processing."""

import unittest
from unittest.mock import patch

import frappe
from frappe.utils import flt

from pos_next.overrides import pricing_rule


def _item(rate, qty=1, rule="TEST-MIN-MAX"):
	return frappe._dict(
		{
			"item_code": f"ITEM-{rate}",
			"price_list_rate": rate,
			"rate": rate,
			"amount": rate * qty,
			"discount_amount": 0,
			"discount_percentage": 0,
			"qty": qty,
			"pricing_rules": rule,
		}
	)


def _rule(apply_on, rate_or_discount="Discount Percentage", qty_limit=1, **values):
	return frappe._dict(
		{
			"name": "TEST-MIN-MAX",
			"price_or_product_discount": "Price",
			"apply_discount_on_price": apply_on,
			"min_or_max_discount_qty_limit": qty_limit,
			"rate_or_discount": rate_or_discount,
			"discount_percentage": values.get("discount_percentage", 0),
			"discount_amount": values.get("discount_amount", 0),
			"rate": values.get("rate", 0),
		}
	)


class TestMinMaxPricing(unittest.TestCase):
	def _apply(self, items, rule, allowed_rules=None):
		doc = frappe._dict({"items": items, "selling_price_list": "Standard Selling"})
		with (
			patch.object(pricing_rule.frappe, "get_cached_doc", return_value=rule),
			patch.object(pricing_rule, "get_applied_pricing_rules", return_value=["TEST-MIN-MAX"]),
		):
			pricing_rule.apply_min_max_price_discounts(doc, allowed_rules=allowed_rules)
		return doc

	def test_min_discounts_only_cheapest_item(self):
		items = [_item(50), _item(80), _item(20)]
		self._apply(items, _rule("Min", discount_percentage=50))

		self.assertAlmostEqual(flt(items[0].rate), 50, places=2)
		self.assertAlmostEqual(flt(items[1].rate), 80, places=2)
		self.assertAlmostEqual(flt(items[2].rate), 10, places=2)
		self.assertAlmostEqual(flt(items[2].discount_percentage), 50, places=2)

	def test_max_respects_partial_quantity_limit(self):
		items = [_item(50), _item(80, qty=3), _item(20)]
		self._apply(
			items,
			_rule("Max", rate_or_discount="Discount Amount", qty_limit=2, discount_amount=10),
		)

		self.assertAlmostEqual(flt(items[1].amount), 220, places=2)
		self.assertAlmostEqual(flt(items[1].discount_amount), 6.67, places=2)
		self.assertAlmostEqual(flt(items[0].rate), 50, places=2)
		self.assertAlmostEqual(flt(items[2].rate), 20, places=2)

	def test_unselected_rule_is_not_applied(self):
		items = [_item(20)]
		self._apply(
			items,
			_rule("Min", discount_percentage=50),
			allowed_rules={"ANOTHER-RULE"},
		)

		self.assertAlmostEqual(flt(items[0].rate), 20, places=2)
		self.assertAlmostEqual(flt(items[0].discount_percentage), 0, places=2)


def run_all():
	suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestMinMaxPricing)
	result = unittest.TextTestRunner(verbosity=2).run(suite)
	return {
		"tests_run": result.testsRun,
		"failures": [str(failure[0]) for failure in result.failures],
		"errors": [str(error[0]) for error in result.errors],
		"was_successful": result.wasSuccessful(),
	}
