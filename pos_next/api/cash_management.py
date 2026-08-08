# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

"""Cashier cash-management: record drawer cash movements (expense / receipt / payment) with a
note, as a Cash Entry Journal Entry linked to the open shift. Gated by the enable_cash_management
feature flag; available to the cashier (not manager-only). The cash account is resolved
server-side from the profile's cash mode of payment — the client only picks the counter account."""

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate

from pos_next.api.feature_flags import require_feature
from pos_next.api.management_scope import assert_company_resource

# Stable internal keys (the UI shows Arabic labels). Expense/Payment take money OUT of the drawer,
# Receipt brings money IN. Notes are required for the money-out types (audit trail).
CASH_ENTRY_TYPES = ("Expense", "Receipt", "Payment")
_NOTES_REQUIRED = {"Expense", "Payment"}
# Counter-account root types allowed per entry type (Expense entries must hit an expense account;
# receipts/payments can legitimately hit any non-drawer account).
_ALLOWED_ROOT_TYPES = {
	"Expense": ["Expense"],
	"Receipt": ["Expense", "Income", "Liability", "Asset", "Equity"],
	"Payment": ["Expense", "Income", "Liability", "Asset", "Equity"],
}


def _cash_context(pos_profile):
	profile = require_feature("cash_management", pos_profile=pos_profile)
	company = frappe.db.get_value("POS Profile", profile, "company")
	return profile, company


def _resolve_cash_account(profile, company):
	"""The drawer's cash account, from the profile's cash mode of payment (settings)."""
	cash_mode = frappe.db.get_value("POS Profile", profile, "posa_cash_mode_of_payment") or "Cash"
	account = frappe.db.get_value("Mode of Payment Account", {"parent": cash_mode, "company": company}, "default_account")
	if not account:
		account = frappe.db.get_value(
			"Account", {"company": company, "account_type": "Cash", "is_group": 0, "disabled": 0}, "name", order_by="creation"
		)
	if not account:
		frappe.throw(_("No cash account is configured for this POS Profile's company. Set the cash Mode of Payment account in Settings."))
	return account, cash_mode


def _current_shift(profile, required=True):
	shift = frappe.db.get_value(
		"POS Opening Shift",
		{"user": frappe.session.user, "pos_profile": profile, "status": "Open", "docstatus": 1},
		"name",
		order_by="period_start_date desc",
	)
	if not shift and required:
		frappe.throw(_("Open a shift before recording cash movements"))
	return shift


@frappe.whitelist()
def get_cash_entry_accounts(entry_type, pos_profile=None):
	"""Counter accounts for the picker, filtered by the entry type."""
	profile, company = _cash_context(pos_profile)
	frappe.has_permission("Account", "read", throw=True)
	if entry_type not in CASH_ENTRY_TYPES:
		frappe.throw(_("Invalid cash entry type"))
	cash_account, _mode = _resolve_cash_account(profile, company)
	accounts = frappe.get_list(
		"Account",
		filters={"company": company, "is_group": 0, "disabled": 0, "root_type": ["in", _ALLOWED_ROOT_TYPES[entry_type]], "name": ["!=", cash_account]},
		fields=["name", "account_name", "account_type", "root_type"],
		order_by="root_type, account_name",
		limit=500,
	)
	return {"accounts": accounts, "currency": frappe.db.get_value("Company", company, "default_currency")}


@frappe.whitelist()
def create_cash_entry(entry_type, amount, account, remarks=None, pos_profile=None):
	profile, company = _cash_context(pos_profile)
	frappe.has_permission("Journal Entry", "create", throw=True)
	frappe.has_permission("Journal Entry", "submit", throw=True)
	if entry_type not in CASH_ENTRY_TYPES:
		frappe.throw(_("Invalid cash entry type"))
	amount = flt(amount)
	if amount <= 0:
		frappe.throw(_("Amount must be greater than zero"))
	remarks = (remarks or "").strip()
	if entry_type in _NOTES_REQUIRED and not remarks:
		frappe.throw(_("A note is required for this cash entry"))

	counter = assert_company_resource("Account", account, company)
	if counter.root_type not in _ALLOWED_ROOT_TYPES[entry_type]:
		frappe.throw(_("The selected account is not valid for this entry type"))
	cash_account, _cash_mode = _resolve_cash_account(profile, company)
	if counter.name == cash_account:
		frappe.throw(_("The account cannot be the drawer's cash account"))
	shift = _current_shift(profile)
	cost_center = frappe.db.get_value("Company", company, "cost_center")

	# Receipt = cash IN (Dr cash / Cr account); Expense & Payment = cash OUT (Dr account / Cr cash).
	if entry_type == "Receipt":
		debit_account, credit_account = cash_account, counter.name
	else:
		debit_account, credit_account = counter.name, cash_account

	journal = frappe.get_doc({
		"doctype": "Journal Entry",
		"voucher_type": "Cash Entry",
		"company": company,
		"posting_date": nowdate(),
		"user_remark": remarks or _("POS cash entry"),
		"posa_pos_opening_shift": shift,
		"posa_cash_entry_type": entry_type,
		"accounts": [
			{"account": debit_account, "debit_in_account_currency": amount, "cost_center": cost_center},
			{"account": credit_account, "credit_in_account_currency": amount, "cost_center": cost_center},
		],
	})
	journal.insert(ignore_permissions=False)
	journal.submit()
	return {
		"name": journal.name,
		"entry_type": entry_type,
		"amount": amount,
		"account": counter.name,
		"account_name": counter.account_name,
		"remarks": remarks,
		"posting_date": str(journal.posting_date),
	}


@frappe.whitelist()
def get_cash_entries(pos_profile=None, limit=50):
	"""Cash entries for the current shift (or today's, when no shift is open)."""
	profile, company = _cash_context(pos_profile)
	frappe.has_permission("Journal Entry", "read", throw=True)
	filters = {"company": company, "posa_cash_entry_type": ["in", list(CASH_ENTRY_TYPES)], "docstatus": 1}
	shift = _current_shift(profile, required=False)
	if shift:
		filters["posa_pos_opening_shift"] = shift
	else:
		filters["posting_date"] = getdate(nowdate())
		filters["owner"] = frappe.session.user
	rows = frappe.get_list(
		"Journal Entry",
		filters=filters,
		fields=["name", "posa_cash_entry_type", "total_debit", "user_remark", "posting_date", "creation"],
		order_by="creation desc",
		limit=min(cint(limit), 100),
	)
	received = sum(flt(r.total_debit) for r in rows if r.posa_cash_entry_type == "Receipt")
	paid = sum(flt(r.total_debit) for r in rows if r.posa_cash_entry_type in ("Expense", "Payment"))
	return {"entries": rows, "received_total": round(received, 2), "paid_total": round(paid, 2), "net_total": round(received - paid, 2)}
