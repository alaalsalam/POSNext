"""Non-destructive, repeatable unit/API runner for Milestone 2."""

import os
import sys
import unittest

import frappe

BENCH_PATH = "/home/erpnext/frappe-bench16"
SITE = "digitpos.trilogy-erp.com"
TEST_MODULES = (
	"pos_next.tests.test_feature_flags",
	"pos_next.tests.test_management_hardening",
	"pos_next.tests.test_supplier_payments",
)


def run():
	os.chdir(BENCH_PATH)
	frappe.init(site=SITE, sites_path=f"{BENCH_PATH}/sites")
	frappe.connect()
	frappe.set_user("Administrator")
	try:
		suite = unittest.TestSuite(
			unittest.defaultTestLoader.loadTestsFromName(module) for module in TEST_MODULES
		)
		result = unittest.TextTestRunner(verbosity=2).run(suite)
		frappe.db.rollback()
		return 0 if result.wasSuccessful() else 1
	finally:
		frappe.destroy()


if __name__ == "__main__":
	sys.exit(run())
