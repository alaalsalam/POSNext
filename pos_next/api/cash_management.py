# Copyright (c) 2026, POS Next and contributors
# For license information, please see license.txt

"""Cashier cash management — a small-business vouchers screen so cashiers don't need Desk.

Records drawer cash movements as a "Cash Entry" Journal Entry linked to the open shift:
  - Expense  : money out to an expense account (chosen via a POS Expense Type, so only the
               configured expense accounts appear — not the whole chart).
  - Receipt  : money in (سند قبض) — optionally from a Customer (party).
  - Payment  : money out (سند صرف) — optionally to an Employee (party).
  - Transfer : move cash between two cash/bank boxes.

Posting mode (POS Settings → posa_cash_posting_mode): "Immediate" submits the entry (posts to the
ledger); "After Approval" saves a draft (no ledger impact) that a MANAGER approves/rejects. The
account for a party entry is derived server-side; the cash box defaults to the profile's cash mode
but can be chosen. Gated by the enable_cash_management feature flag; cashier-available.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate

from pos_next.api.feature_flags import get_feature_flags, is_feature_manager, require_feature
from pos_next.api.management_scope import (
	assert_company_resource,
	assert_doc_permission,
	require_manager_feature,
)

CASH_ENTRY_TYPES = ("Expense", "Receipt", "Payment", "Transfer")
_NOTES_REQUIRED = {"Expense", "Payment"}
# Party types allowed per entry type (empty = no party).
_PARTY_TYPES = {"Receipt": ("Customer",), "Payment": ("Employee",), "Expense": (), "Transfer": ()}
_PARTY_NAME_FIELD = {"Customer": "customer_name", "Employee": "employee_name"}


def _cash_context(pos_profile):
	profile = require_feature("cash_management", pos_profile=pos_profile)
	company = frappe.db.get_value("POS Profile", profile, "company")
	return profile, company


def _posting_mode(profile):
	return frappe.db.get_value("POS Settings", {"pos_profile": profile}, "posa_cash_posting_mode") or "Immediate"


def _default_cash_account(profile, company):
	cash_mode = frappe.db.get_value("POS Profile", profile, "posa_cash_mode_of_payment") or "Cash"
	account = frappe.db.get_value("Mode of Payment Account", {"parent": cash_mode, "company": company}, "default_account")
	if not account:
		account = frappe.db.get_value(
			"Account", {"company": company, "account_type": "Cash", "is_group": 0, "disabled": 0}, "name", order_by="creation"
		)
	return account


def _resolve_cash_box(profile, company, cash_account):
	"""The cash/bank box for the movement — the chosen one, else the profile's default cash account."""
	if cash_account:
		box = assert_company_resource("Account", cash_account, company)
		if box.account_type not in ("Cash", "Bank"):
			frappe.throw(_("The cash box must be a Cash or Bank account"))
		return box.name
	box = _default_cash_account(profile, company)
	if not box:
		frappe.throw(_("No cash account is configured for this POS Profile's company. Set the cash Mode of Payment account in Settings."))
	return box


def _resolve_expense_account(expense_type, company):
	row = frappe.db.get_value("POS Expense Type", expense_type, ["expense_account", "company", "enabled"], as_dict=True)
	if not row or not row.enabled or row.company != company:
		frappe.throw(_("Select a valid expense type"))
	return row.expense_account


def _resolve_party_account(party_type, party, company):
	from erpnext.accounts.party import get_party_account

	account = get_party_account(party_type, party, company)
	if not account:
		frappe.throw(_("No default account is configured for {0} {1}").format(_(party_type), party))
	return account


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
def get_cash_management_setup(pos_profile=None):
	"""Everything the panel needs on open: posting mode, the drawer's cash boxes, expense types."""
	profile, company = _cash_context(pos_profile)
	frappe.has_permission("Account", "read", throw=True)
	boxes = frappe.get_list(
		"Account",
		filters={"company": company, "is_group": 0, "disabled": 0, "account_type": ["in", ["Cash", "Bank"]]},
		fields=["name", "account_name", "account_type"],
		order_by="account_type, account_name",
		limit=200,
	)
	expense_types = frappe.get_list(
		"POS Expense Type",
		filters={"company": company, "enabled": 1},
		fields=["name", "expense_type_name"],
		order_by="expense_type_name",
		limit=500,
	)
	# Expense-type editing is its own capability (enable_expense_types + manager) — the nested
	# gear/empty-state entry points show only when the cashier's manager may actually manage types.
	expense_types_enabled = cint(
		frappe.db.get_value("POS Settings", {"pos_profile": profile, "enabled": 1}, "enable_expense_types")
	)
	return {
		"posting_mode": _posting_mode(profile),
		"is_manager": bool(is_feature_manager()),
		"can_manage_expense_types": bool(is_feature_manager()) and bool(expense_types_enabled),
		"default_cash_account": _default_cash_account(profile, company),
		"cash_boxes": boxes,
		"expense_types": expense_types,
		"currency": frappe.db.get_value("Company", company, "default_currency"),
	}


@frappe.whitelist()
def get_cash_entry_accounts(entry_type, pos_profile=None):
	"""Counter accounts for a general (party-less) Receipt/Payment — expense entries use a type,
	transfers use cash boxes, so those don't call this."""
	profile, company = _cash_context(pos_profile)
	frappe.has_permission("Account", "read", throw=True)
	if entry_type not in ("Receipt", "Payment"):
		frappe.throw(_("Select an account only for a general receipt or payment"))
	cash_account = _default_cash_account(profile, company)
	accounts = frappe.get_list(
		"Account",
		filters={"company": company, "is_group": 0, "disabled": 0, "name": ["!=", cash_account]},
		fields=["name", "account_name", "account_type", "root_type"],
		order_by="root_type, account_name",
		limit=500,
	)
	return {"accounts": accounts}


@frappe.whitelist()
def get_parties(party_type, search="", pos_profile=None):
	"""Party options for a receipt/payment (Customer / Employee / Supplier)."""
	_cash_context(pos_profile)
	if party_type not in _PARTY_NAME_FIELD:
		frappe.throw(_("Invalid party type"))
	frappe.has_permission(party_type, "read", throw=True)
	name_field = _PARTY_NAME_FIELD[party_type]
	filters = {}
	if search:
		filters[name_field] = ["like", f"%{search}%"]
	rows = frappe.get_list(party_type, filters=filters, fields=["name", f"{name_field} as party_name"], order_by=name_field, limit=20)
	return {"parties": rows}


@frappe.whitelist()
def create_cash_entry(
	entry_type,
	amount,
	pos_profile=None,
	cash_account=None,
	to_account=None,
	account=None,
	expense_type=None,
	party_type=None,
	party=None,
	remarks=None,
):
	profile, company = _cash_context(pos_profile)
	frappe.has_permission("Journal Entry", "create", throw=True)
	if entry_type not in CASH_ENTRY_TYPES:
		frappe.throw(_("Invalid cash entry type"))
	amount = flt(amount)
	if amount <= 0:
		frappe.throw(_("Amount must be greater than zero"))
	remarks = (remarks or "").strip()
	if entry_type in _NOTES_REQUIRED and not remarks:
		frappe.throw(_("A note is required for this cash entry"))

	box = _resolve_cash_box(profile, company, cash_account)
	party_row = None

	if entry_type == "Transfer":
		destination = assert_company_resource("Account", to_account, company)
		if destination.account_type not in ("Cash", "Bank"):
			frappe.throw(_("The destination must be a Cash or Bank account"))
		if destination.name == box:
			frappe.throw(_("The source and destination cash boxes must differ"))
		debit_account, credit_account = destination.name, box  # Dr to-box / Cr from-box
	elif entry_type == "Expense":
		expense_account = _resolve_expense_account(expense_type, company)
		debit_account, credit_account = expense_account, box  # Dr expense / Cr cash
	else:
		# Receipt / Payment — party (derives its account) OR a general account.
		if party_type or party:
			if party_type not in _PARTY_TYPES[entry_type]:
				frappe.throw(_("This party type is not allowed for this entry"))
			if not party:
				frappe.throw(_("Select a {0}").format(_(party_type)))
			assert_doc_permission(party_type, party)
			counter_account = _resolve_party_account(party_type, party, company)
			party_row = (party_type, party)
		else:
			counter = assert_company_resource("Account", account, company)
			counter_account = counter.name
		if counter_account == box:
			frappe.throw(_("The account cannot be the drawer's cash box"))
		if entry_type == "Receipt":
			debit_account, credit_account = box, counter_account  # Dr cash / Cr account
		else:
			debit_account, credit_account = counter_account, box  # Dr account / Cr cash

	shift = _current_shift(profile)
	cost_center = frappe.db.get_value("Company", company, "cost_center")

	def _line(acct, debit, credit):
		row = {"account": acct, "debit_in_account_currency": debit, "credit_in_account_currency": credit, "cost_center": cost_center}
		# The party attaches to the non-cash counter row.
		if party_row and acct not in (box,):
			row["party_type"], row["party"] = party_row
		return row

	journal = frappe.get_doc({
		"doctype": "Journal Entry",
		"voucher_type": "Cash Entry",
		"company": company,
		"posting_date": nowdate(),
		"user_remark": remarks or _("POS cash entry"),
		"posa_pos_opening_shift": shift,
		"posa_cash_entry_type": entry_type,
		"accounts": [_line(debit_account, amount, 0), _line(credit_account, 0, amount)],
	})
	journal.insert(ignore_permissions=False)

	submitted = False
	if _posting_mode(profile) == "Immediate":
		frappe.has_permission("Journal Entry", "submit", throw=True)
		journal.submit()
		submitted = True

	return {
		"name": journal.name,
		"entry_type": entry_type,
		"amount": amount,
		"remarks": remarks,
		"posting_date": str(journal.posting_date),
		"status": "Approved" if submitted else "Pending Approval",
		"docstatus": journal.docstatus,
	}


def _get_cash_entry(name, profile, company, ptype="read"):
	journal = assert_doc_permission("Journal Entry", name, ptype)
	if journal.company != company or not journal.get("posa_cash_entry_type"):
		frappe.throw(_("This is not a POS cash entry"), frappe.PermissionError)
	if journal.get("posa_pos_opening_shift") and not frappe.db.exists(
		"POS Opening Shift", {"name": journal.posa_pos_opening_shift, "pos_profile": profile}
	):
		frappe.throw(_("This cash entry belongs to a different POS Profile"), frappe.PermissionError)
	return journal


@frappe.whitelist()
def approve_cash_entry(name, pos_profile=None):
	"""Post a pending (draft) cash entry to the ledger. Manager only."""
	profile, company = _cash_context(pos_profile)
	if not is_feature_manager():
		frappe.throw(_("Only a POS manager can approve cash entries"), frappe.PermissionError)
	frappe.has_permission("Journal Entry", "submit", throw=True)
	journal = _get_cash_entry(name, profile, company, "submit")
	if journal.docstatus != 0:
		frappe.throw(_("Only pending cash entries can be approved"))
	journal.submit()
	return {"name": journal.name, "status": "Approved", "docstatus": journal.docstatus}


@frappe.whitelist()
def reject_cash_entry(name, pos_profile=None):
	"""Discard a pending (draft) cash entry. Manager only."""
	profile, company = _cash_context(pos_profile)
	if not is_feature_manager():
		frappe.throw(_("Only a POS manager can reject cash entries"), frappe.PermissionError)
	frappe.has_permission("Journal Entry", "delete", throw=True)
	journal = _get_cash_entry(name, profile, company, "delete")
	if journal.docstatus != 0:
		frappe.throw(_("Only pending cash entries can be rejected"))
	frappe.delete_doc("Journal Entry", journal.name, ignore_permissions=False)
	return {"name": name, "status": "Rejected"}


@frappe.whitelist()
def get_cash_entries(pos_profile=None, limit=50):
	"""Cash entries for the current shift (or today's) — both posted and pending."""
	profile, company = _cash_context(pos_profile)
	frappe.has_permission("Journal Entry", "read", throw=True)
	filters = {"company": company, "posa_cash_entry_type": ["in", list(CASH_ENTRY_TYPES)], "docstatus": ["<", 2]}
	shift = _current_shift(profile, required=False)
	if shift:
		filters["posa_pos_opening_shift"] = shift
	else:
		filters["posting_date"] = getdate(nowdate())
		filters["owner"] = frappe.session.user
	rows = frappe.get_list(
		"Journal Entry",
		filters=filters,
		fields=["name", "posa_cash_entry_type", "total_debit", "user_remark", "posting_date", "creation", "docstatus"],
		order_by="creation desc",
		limit=min(cint(limit), 100),
	)
	for row in rows:
		row["status"] = "Approved" if row.docstatus == 1 else "Pending Approval"
	posted = [r for r in rows if r.docstatus == 1]
	received = sum(flt(r.total_debit) for r in posted if r.posa_cash_entry_type == "Receipt")
	paid = sum(flt(r.total_debit) for r in posted if r.posa_cash_entry_type in ("Expense", "Payment"))
	pending = sum(1 for r in rows if r.docstatus == 0)
	return {
		"entries": rows,
		"received_total": round(received, 2),
		"paid_total": round(paid, 2),
		"net_total": round(received - paid, 2),
		"pending_count": pending,
		"is_manager": bool(is_feature_manager()),
	}


# ── Expense type management (manager-only) ──────────────────────────────────────────────────
# A manager defines the expense types (and the account each posts to) from the app so cashiers
# never touch Desk or the full chart of accounts. Company-scoped: a type is bound to the POS
# Profile's company and its account is validated against it by the POS Expense Type controller.


def _assert_cash_manager(pos_profile):
	"""Expense-type management is an INDEPENDENT capability: it needs its own enable_expense_types
	flag plus a manager role — not the cash_management flag. A business can pre-configure expense
	types without giving cashiers the drawer panel, or run the drawer without exposing type editing."""
	return require_manager_feature("expense_types", pos_profile=pos_profile)


@frappe.whitelist()
def get_expense_types(pos_profile=None):
	"""Every expense type (enabled and disabled) of the profile's company, for the manager screen."""
	profile, company = _assert_cash_manager(pos_profile)
	frappe.has_permission("POS Expense Type", "read", throw=True)
	rows = frappe.get_list(
		"POS Expense Type",
		filters={"company": company},
		fields=["name", "expense_type_name", "expense_account", "enabled"],
		order_by="expense_type_name",
		limit=500,
	)
	if rows:
		names = {r.expense_account for r in rows}
		account_names = {
			a.name: a.account_name
			for a in frappe.get_all("Account", filters={"name": ["in", list(names)]}, fields=["name", "account_name"])
		}
		for r in rows:
			r["account_name"] = account_names.get(r.expense_account, r.expense_account)
	return {"expense_types": rows, "company": company}


@frappe.whitelist()
def get_expense_accounts(pos_profile=None):
	"""The company's non-group, enabled Expense accounts — the scoped picker for a type, so the
	manager never has to scroll the whole chart of accounts."""
	profile, company = _assert_cash_manager(pos_profile)
	frappe.has_permission("Account", "read", throw=True)
	accounts = frappe.get_list(
		"Account",
		filters={"company": company, "root_type": "Expense", "is_group": 0, "disabled": 0},
		fields=["name", "account_name"],
		order_by="account_name",
		limit=1000,
	)
	return {"accounts": accounts, "company": company}


@frappe.whitelist()
def save_expense_type(expense_type_name, expense_account, pos_profile=None, enabled=1, name=None):
	"""Create or update an expense type. The company is always the profile's — a manager can never
	create a type for, or move one to, another company. Account rules are enforced by the controller."""
	profile, company = _assert_cash_manager(pos_profile)
	expense_type_name = (expense_type_name or "").strip()
	if not expense_type_name:
		frappe.throw(_("Enter an expense type name"))
	if not expense_account:
		frappe.throw(_("Select an expense account"))

	if name:
		if frappe.db.get_value("POS Expense Type", name, "company") != company:
			frappe.throw(_("This expense type belongs to a different company"), frappe.PermissionError)
		doc = frappe.get_doc("POS Expense Type", name)
		doc.expense_type_name = expense_type_name
		doc.expense_account = expense_account
		doc.enabled = cint(enabled)
		doc.save()
	else:
		doc = frappe.get_doc({
			"doctype": "POS Expense Type",
			"expense_type_name": expense_type_name,
			"company": company,
			"expense_account": expense_account,
			"enabled": cint(enabled),
		})
		doc.insert()

	return {
		"name": doc.name,
		"expense_type_name": doc.expense_type_name,
		"expense_account": doc.expense_account,
		"enabled": cint(doc.enabled),
	}


@frappe.whitelist()
def delete_expense_type(name, pos_profile=None):
	"""Remove an expense type. Past cash entries store the resolved account, not this link, so a
	delete never rewrites history."""
	profile, company = _assert_cash_manager(pos_profile)
	existing_company = frappe.db.get_value("POS Expense Type", name, "company")
	if not existing_company:
		frappe.throw(_("Expense type not found"))
	if existing_company != company:
		frappe.throw(_("This expense type belongs to a different company"), frappe.PermissionError)
	frappe.has_permission("POS Expense Type", "delete", throw=True)
	frappe.delete_doc("POS Expense Type", name)
	return {"name": name, "deleted": True}
