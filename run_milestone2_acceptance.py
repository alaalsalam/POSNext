"""Transactional ERPNext acceptance for Milestone 2.

All QA masters and transactions are rolled back. Feature flags are asserted back at their
original secure-off state before the process exits.
"""

import os
import sys
import time
import traceback

import frappe
from frappe.utils import flt, nowdate

from pos_next.api import catalog, purchases

BENCH_PATH = "/home/erpnext/frappe-bench16"
SITE = "digitpos.trilogy-erp.com"


def check(condition, message):
	if not condition:
		raise AssertionError(message)


def gl_balance(voucher_type, voucher_no):
	rows = frappe.get_all(
		"GL Entry",
		filters={"voucher_type": voucher_type, "voucher_no": voucher_no, "is_cancelled": 0},
		fields=["debit", "credit"],
		limit=0,
	)
	return rows, sum(flt(row.debit) - flt(row.credit) for row in rows)


def find_profile():
	for settings in frappe.get_all(
		"POS Settings", filters={"enabled": 1}, fields=["name", "pos_profile"], limit=0
	):
		profile = frappe.get_doc("POS Profile", settings.pos_profile)
		if profile.disabled or not profile.warehouse or not profile.selling_price_list or not profile.item_groups:
			continue
		if not frappe.db.exists("Warehouse", {"name": profile.warehouse, "company": profile.company, "is_group": 0}):
			continue
		return settings, profile
	raise AssertionError("No enabled development POS Profile has settings, warehouse, price list, and item groups")


def create_qa_user(email, role, profile, company):
	user = frappe.get_doc({
		"doctype": "User",
		"email": email,
		"first_name": "POSNext QA",
		"send_welcome_email": 0,
		"roles": [{"role": role}],
	}).insert(ignore_permissions=True)
	frappe.get_doc({
		"doctype": "User Permission",
		"user": user.name,
		"allow": "Company",
		"for_value": company,
		"apply_to_all_doctypes": 1,
	}).insert(ignore_permissions=True)
	profile.append("applicable_for_users", {"user": user.name})
	return user


def run_acceptance():
	settings, profile = find_profile()
	flags = ("enable_catalog_management", "enable_purchases", "enable_supplier_payments")
	original_flags = {field: int(settings.get(field) or 0) for field in flags}
	check(not any(original_flags.values()), "Milestone flags were not OFF before acceptance")
	stamp = str(int(time.time()))
	prefix = f"POSNEXT-QA-{stamp}"
	evidence = {"profile": profile.name, "company": profile.company, "qa_prefix": prefix}

	for field in flags:
		frappe.db.set_value("POS Settings", settings.name, field, 1, update_modified=False)

	allowed_group = profile.item_groups[0].item_group
	allowed_doc = frappe.get_doc("Item Group", allowed_group)
	parent_group = allowed_doc.parent_item_group
	check(parent_group and frappe.db.get_value("Item Group", parent_group, "is_group"), "Profile item group has no valid parent")
	group = catalog.create_item_group(f"{prefix}-GROUP", parent_group, profile.name)
	profile.reload()
	check(any(row.item_group == group["name"] for row in profile.item_groups), "New Item Group was not scoped to the POS Profile")

	uom = frappe.db.get_value("UOM", {"enabled": 1}, "name")
	stock_item = catalog.create_quick_item(
		f"{prefix}-STOCK",
		group["name"],
		item_code=f"{prefix}-STOCK",
		price=25,
		buying_price=10,
		stock_uom=uom,
		is_stock_item=1,
		barcode=f"9{stamp[-11:]}",
		pos_profile=profile.name,
	)
	nonstock_item = catalog.create_quick_item(
		f"{prefix}-SERVICE",
		group["name"],
		item_code=f"{prefix}-SERVICE",
		price=20,
		buying_price=8,
		stock_uom=uom,
		is_stock_item=0,
		pos_profile=profile.name,
	)
	prices_before = catalog.get_item_prices(stock_item["item_code"], profile.name)["all_prices"]
	update_one = catalog.update_item_prices(stock_item["item_code"], buying_price=11, uom=uom, pos_profile=profile.name)
	update_two = catalog.update_item_prices(stock_item["item_code"], buying_price=11, uom=uom, pos_profile=profile.name)
	prices_after = catalog.get_item_prices(stock_item["item_code"], profile.name)["all_prices"]
	check(update_one["prices"][0]["name"] == update_two["prices"][0]["name"], "Item Price retry created a duplicate")
	check(len(prices_before) == len(prices_after), "Item Price count changed during idempotent update")
	evidence["catalog"] = {"group": group["name"], "items": [stock_item["item_code"], nonstock_item["item_code"]], "price_rows": len(prices_after)}

	supplier_group = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name")
	supplier = purchases.create_supplier(f"{prefix}-SUPPLIER", supplier_group, "Company", profile.name)
	defaults = purchases.get_new_purchase_invoice_defaults(profile.name)
	manager = create_qa_user(f"manager-{stamp}@posnext.qa", "POS Manager", profile, profile.company)
	cashier = create_qa_user(f"cashier-{stamp}@posnext.qa", "POSNext Cashier", profile, profile.company)
	profile.save(ignore_permissions=False)
	foreign_profile = frappe.db.get_value("POS Profile", {"name": ["!=", profile.name], "company": ["!=", profile.company]}, "name")
	check(foreign_profile, "No foreign-company POS Profile exists for isolation acceptance")
	frappe.set_user(manager.name)
	check(catalog.get_catalog_defaults(profile.name)["company"] == profile.company, "POS Manager could not read scoped catalog defaults")
	check(purchases.get_new_purchase_invoice_defaults(profile.name)["company"] == profile.company, "POS Manager could not read scoped purchase defaults")
	check(all(row.company == profile.company for row in purchases.get_warehouses(profile.name)), "Warehouse list leaked another company")
	try:
		catalog.get_catalog_defaults(foreign_profile)
		raise AssertionError("POS Manager accessed a foreign POS Profile")
	except frappe.PermissionError:
		pass
	frappe.set_user(cashier.name)
	try:
		catalog.get_catalog_defaults(profile.name)
		raise AssertionError("Cashier bypassed catalog manager enforcement")
	except frappe.PermissionError:
		pass
	try:
		purchases.get_purchase_invoices(pos_profile=profile.name)
		raise AssertionError("Cashier bypassed purchases manager enforcement")
	except frappe.PermissionError:
		pass
	frappe.set_user("Administrator")
	evidence["security"] = {"manager": manager.name, "cashier": cashier.name, "foreign_profile_denied": foreign_profile}
	tax_account = frappe.db.get_value(
		"Account",
		{"company": profile.company, "is_group": 0, "disabled": 0, "root_type": "Expense", "account_name": ["like", "%Tax%"]},
		"name",
	)
	check(tax_account, "Development company has no permitted tax expense account")
	base_payload = {
		"supplier": supplier["name"],
		"company": profile.company,
		"posting_date": nowdate(),
		"due_date": nowdate(),
		"bill_date": nowdate(),
		"currency": defaults["currency"],
		"buying_price_list": defaults["buying_price_list"],
	}

	nonstock_key = f"purchase-{prefix}-nonstock"
	nonstock_payload = {
			**base_payload,
			"bill_no": f"{prefix}-NS",
			"update_stock": 0,
			"items": [{"item_code": nonstock_item["item_code"], "qty": 2, "uom": uom, "rate": 8}],
			"taxes": [{"charge_type": "On Net Total", "account_head": tax_account, "description": "QA purchase tax", "rate": 15, "add_deduct_tax": "Add"}],
		}
	nonstock = purchases.save_purchase_invoice(
		nonstock_payload,
		idempotency_key=nonstock_key,
		pos_profile=profile.name,
	)
	nonstock_retry = purchases.save_purchase_invoice(
		nonstock_payload,
		idempotency_key=nonstock_key,
		pos_profile=profile.name,
	)
	check(nonstock_retry["name"] == nonstock["name"] and nonstock_retry["idempotent_replay"], "Purchase retry was not idempotent")
	conflicting_purchase_requests = (
		{**nonstock_payload, "remarks": "changed retry"},
		{**nonstock_payload, "discount_amount": 1},
		{**nonstock_payload, "posting_date": frappe.utils.add_days(nowdate(), -1)},
		{**nonstock_payload, "taxes": [{**nonstock_payload["taxes"][0], "rate": 5}]},
	)
	for conflict in conflicting_purchase_requests:
		try:
			purchases.save_purchase_invoice(
				conflict,
				idempotency_key=nonstock_key,
				pos_profile=profile.name,
			)
			raise AssertionError("Purchase retry accepted a changed material request")
		except frappe.ValidationError:
			pass
	nonstock = purchases.submit_purchase_invoice(nonstock["name"], nonstock["modified"], profile.name)
	ns_gl, ns_balance = gl_balance("Purchase Invoice", nonstock["name"])
	check(ns_gl and abs(ns_balance) < 0.01, "Non-stock Purchase Invoice GL is not balanced")
	check(abs(flt(nonstock["total_taxes_and_charges"]) - 2.4) < 0.01, "Purchase tax does not reconcile to 15% of net total")
	check(not frappe.db.exists("Stock Ledger Entry", {"voucher_type": "Purchase Invoice", "voucher_no": nonstock["name"], "is_cancelled": 0}), "Non-stock purchase created Stock Ledger Entries")

	stock = purchases.save_purchase_invoice(
		{
			**base_payload,
			"bill_no": f"{prefix}-ST",
			"update_stock": 1,
			"set_warehouse": profile.warehouse,
			"items": [{"item_code": stock_item["item_code"], "qty": 3, "uom": uom, "rate": 11, "warehouse": profile.warehouse}],
		},
		idempotency_key=f"purchase-{prefix}-stock",
		pos_profile=profile.name,
	)
	stock = purchases.submit_purchase_invoice(stock["name"], stock["modified"], profile.name)
	stock_gl, stock_balance = gl_balance("Purchase Invoice", stock["name"])
	stock_qty = sum(
		flt(row.actual_qty)
		for row in frappe.get_all(
			"Stock Ledger Entry",
			filters={"voucher_type": "Purchase Invoice", "voucher_no": stock["name"], "is_cancelled": 0},
			fields=["actual_qty"],
			limit=0,
		)
	)
	check(stock_gl and abs(stock_balance) < 0.01, "Stock Purchase Invoice GL is not balanced")
	check(abs(stock_qty - 3) < 0.001, "Stock Ledger quantity does not reconcile to purchase quantity")

	foreign = None
	if defaults["currency"] != "USD" and frappe.db.exists("Currency", {"name": "USD", "enabled": 1}):
		foreign_price_list = frappe.get_doc({
			"doctype": "Price List",
			"price_list_name": f"{prefix}-USD-BUYING",
			"currency": "USD",
			"buying": 1,
			"selling": 0,
			"enabled": 1,
		}).insert(ignore_permissions=False)
		foreign = purchases.save_purchase_invoice(
			{
				**base_payload,
				"bill_no": f"{prefix}-FX",
				"currency": "USD",
				"conversion_rate": 3.75,
				"plc_conversion_rate": 1,
				"buying_price_list": foreign_price_list.name,
				"update_stock": 0,
				"items": [{"item_code": nonstock_item["item_code"], "qty": 1, "uom": uom, "rate": 10}],
			},
			idempotency_key=f"purchase-{prefix}-foreign",
			pos_profile=profile.name,
		)
		foreign = purchases.submit_purchase_invoice(foreign["name"], foreign["modified"], profile.name)
		foreign_gl, foreign_balance = gl_balance("Purchase Invoice", foreign["name"])
		check(foreign_gl and abs(foreign_balance) < 0.01, "Foreign-currency Purchase Invoice GL is not balanced")

	payment_defaults = purchases.get_supplier_payment_defaults(nonstock["name"], profile.name)
	check(payment_defaults["accounts"], "No permitted Cash/Bank account exists for acceptance")
	paid_from = payment_defaults["accounts"][0]["name"]
	initial_outstanding = flt(nonstock["outstanding_amount"])
	partial = round(initial_outstanding / 2, 2)
	payment = purchases.create_supplier_payment(
		nonstock["name"], partial, paid_from,
		idempotency_key=f"payment-{prefix}-partial",
		reference_no=f"{prefix}-P1",
		pos_profile=profile.name,
	)
	payment_retry = purchases.create_supplier_payment(
		nonstock["name"], partial, paid_from,
		idempotency_key=f"payment-{prefix}-partial",
		reference_no=f"{prefix}-P1",
		pos_profile=profile.name,
	)
	check(payment_retry["name"] == payment["name"] and payment_retry["idempotent_replay"], "Payment retry was not idempotent")
	for conflict in (
		{"reference_no": f"{prefix}-CHANGED"},
		{"reference_no": f"{prefix}-P1", "remarks": "changed retry"},
		{"reference_no": f"{prefix}-P1", "posting_date": frappe.utils.add_days(nowdate(), -1)},
	):
		try:
			purchases.create_supplier_payment(
				nonstock["name"], partial, paid_from,
				idempotency_key=f"payment-{prefix}-partial",
				pos_profile=profile.name,
				**conflict,
			)
			raise AssertionError("Payment retry accepted a changed material request")
		except frappe.ValidationError:
			pass
	payment = purchases.submit_supplier_payment(payment["name"], payment["modified"], profile.name)
	after_partial = flt(frappe.db.get_value("Purchase Invoice", nonstock["name"], "outstanding_amount"))
	check(abs(after_partial - (initial_outstanding - partial)) < 0.01, "Partial payment outstanding does not reconcile")
	pay_gl, pay_balance = gl_balance("Payment Entry", payment["name"])
	check(pay_gl and abs(pay_balance) < 0.01, "Partial Payment Entry GL is not balanced")
	check(frappe.db.exists("Payment Ledger Entry", {"voucher_type": "Payment Entry", "voucher_no": payment["name"], "delinked": 0}), "Payment Ledger Entry was not created")

	full = purchases.create_supplier_payment(
		nonstock["name"], after_partial, paid_from,
		idempotency_key=f"payment-{prefix}-full",
		reference_no=f"{prefix}-P2",
		submit=1,
		pos_profile=profile.name,
	)
	check(abs(flt(frappe.db.get_value("Purchase Invoice", nonstock["name"], "outstanding_amount"))) < 0.01, "Full payment did not clear outstanding")
	purchases.cancel_supplier_payment(full["name"], profile.name)
	check(abs(flt(frappe.db.get_value("Purchase Invoice", nonstock["name"], "outstanding_amount")) - after_partial) < 0.01, "Full payment cancellation did not restore outstanding")
	purchases.cancel_supplier_payment(payment["name"], profile.name)
	check(abs(flt(frappe.db.get_value("Purchase Invoice", nonstock["name"], "outstanding_amount")) - initial_outstanding) < 0.01, "Partial payment cancellation did not restore outstanding")

	purchases.cancel_purchase_invoice(stock["name"], profile.name)
	check(not frappe.db.exists("Stock Ledger Entry", {"voucher_type": "Purchase Invoice", "voucher_no": stock["name"], "is_cancelled": 0}), "Stock cancellation left active Stock Ledger Entries")
	purchases.cancel_purchase_invoice(nonstock["name"], profile.name)
	if foreign:
		purchases.cancel_purchase_invoice(foreign["name"], profile.name)
	evidence["purchases"] = {"nonstock": nonstock["name"], "stock": stock["name"], "foreign_currency": foreign["name"] if foreign else None, "gl_entries": len(ns_gl) + len(stock_gl), "stock_qty_before_cancel": stock_qty}
	evidence["payments"] = {"partial": payment["name"], "full": full["name"], "initial_outstanding": initial_outstanding, "after_partial": after_partial, "final_before_invoice_cancel": initial_outstanding}
	return evidence, settings.name, original_flags


def main():
	os.chdir(BENCH_PATH)
	frappe.init(site=SITE, sites_path=f"{BENCH_PATH}/sites")
	frappe.connect()
	frappe.set_user("Administrator")
	settings_name = None
	original_flags = None
	try:
		evidence, settings_name, original_flags = run_acceptance()
		print(evidence)
		return 0
	except Exception:
		traceback.print_exc()
		return 1
	finally:
		frappe.db.rollback()
		if settings_name and original_flags is not None:
			actual = frappe.db.get_value("POS Settings", settings_name, list(original_flags), as_dict=True)
			assert all(int(actual.get(field) or 0) == value for field, value in original_flags.items())
			print({"flags_after_rollback": dict(actual)})
		frappe.destroy()


if __name__ == "__main__":
	sys.exit(main())
