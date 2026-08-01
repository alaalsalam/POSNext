# Copyright (c) 2025, POS Next and contributors
# For license information, please see license.txt

"""Manager-only, profile-scoped reporting APIs for the Digit POS dashboard."""

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, get_datetime, getdate, nowdate

from pos_next.api.reporting_access import (
	assert_report_manager,
	authorize_report,
	get_reportable_profiles,
)

DESK_REPORTS = (
	"Sales vs Shifts Report",
	"Cashier Performance Report",
	"Payments and Cash Control Report",
	"Inventory Impact and Fast Movers Report",
	"Offline Sync and System Health Report",
)


def _date_range(period, from_date=None, to_date=None):
	today = nowdate()
	if period == "today" or (not period and not from_date):
		return today, today
	if period == "yesterday":
		yesterday = add_days(today, -1)
		return yesterday, yesterday
	if period == "this_week":
		from frappe.utils import get_first_day_of_week

		return str(get_first_day_of_week(today)), today
	if period == "this_month":
		from frappe.utils import get_first_day

		return str(get_first_day(today)), today
	if period == "custom" and from_date and to_date:
		start, end = getdate(from_date), getdate(to_date)
		if start > end:
			frappe.throw(_("From Date cannot be after To Date"))
		return str(start), str(end)
	return today, today


def _get_invoice_names(pos_profile, from_date, to_date, include_returns=True):
	company = frappe.db.get_value("POS Profile", pos_profile, "company")
	filters = {
		"docstatus": 1,
		"is_pos": 1,
		"pos_profile": pos_profile,
		"company": company,
		"posting_date": ["between", [from_date, to_date]],
	}
	if not include_returns:
		filters["is_return"] = 0
	return frappe.get_all(
		"Sales Invoice",
		filters=filters,
		fields=[
			"name",
			"grand_total",
			"net_total",
			"total_taxes_and_charges",
			"rounding_adjustment",
			"is_return",
			"posting_date",
			"posting_time",
			"customer",
			"outstanding_amount",
			"paid_amount",
			"currency",
		],
		order_by="posting_date desc, posting_time desc, name desc",
		limit=0,
	)


def _authorize(pos_profile):
	return authorize_report({"pos_profile": pos_profile})


@frappe.whitelist()
def get_report_filters():
	profiles = get_reportable_profiles()
	return {
		"pos_profiles": profiles,
		"periods": [
			{"key": "today", "label": _("Today")},
			{"key": "yesterday", "label": _("Yesterday")},
			{"key": "this_week", "label": _("This Week")},
			{"key": "this_month", "label": _("This Month")},
			{"key": "custom", "label": _("Custom Range")},
		],
		"desk_reports": [{"name": name, "label": _(name)} for name in DESK_REPORTS],
	}


@frappe.whitelist()
def get_daily_summary(pos_profile, period="today", from_date=None, to_date=None):
	_authorize(pos_profile)
	fd, td = _date_range(period, from_date, to_date)
	invoices = _get_invoice_names(pos_profile, fd, td)

	sales = [invoice for invoice in invoices if not invoice.is_return]
	returns = [invoice for invoice in invoices if invoice.is_return]
	sales_total = sum(flt(invoice.grand_total) for invoice in sales)
	returns_total = sum(abs(flt(invoice.grand_total)) for invoice in returns)
	net_sales = sum(flt(invoice.grand_total) for invoice in invoices)
	net_total = sum(flt(invoice.net_total) for invoice in invoices)
	tax_total = sum(flt(invoice.total_taxes_and_charges) for invoice in invoices)
	rounding_total = sum(flt(invoice.rounding_adjustment) for invoice in invoices)
	# ERPNext grand_total is pre-rounding; rounded_total is grand_total + rounding_adjustment.
	component_difference = net_sales - net_total - tax_total

	return {
		"from_date": fd,
		"to_date": td,
		"pos_profile": pos_profile,
		"sales_total": round(sales_total, 2),
		"sales_count": len(sales),
		"avg_invoice": round(sales_total / len(sales), 2) if sales else 0.0,
		"returns_total": round(returns_total, 2),
		"returns_count": len(returns),
		"outstanding_total": round(sum(max(flt(invoice.outstanding_amount), 0) for invoice in sales), 2),
		"net_sales": round(net_sales, 2),
		"net_total": round(net_total, 2),
		"tax_total": round(tax_total, 2),
		"rounding_adjustment": round(rounding_total, 2),
		"reconciliation_difference": round(component_difference, 2),
		"reconciled": abs(component_difference) < 0.01,
		"currency": frappe.db.get_value("POS Profile", pos_profile, "currency") or "SAR",
	}


@frappe.whitelist()
def get_payment_breakdown(pos_profile, period="today", from_date=None, to_date=None):
	_authorize(pos_profile)
	fd, td = _date_range(period, from_date, to_date)
	invoices = _get_invoice_names(pos_profile, fd, td, include_returns=False)
	if not invoices:
		return {"from_date": fd, "to_date": td, "methods": [], "invoice_total": 0.0, "paid_total": 0.0}

	invoice_names = [invoice.name for invoice in invoices]
	rows = frappe.get_all(
		"Sales Invoice Payment",
		filters={"parent": ["in", invoice_names], "parenttype": "Sales Invoice"},
		fields=["parent", "mode_of_payment", "amount"],
		limit=0,
	)
	method_map = {}
	for row in rows:
		mode = row.mode_of_payment or _("Unspecified")
		data = method_map.setdefault(mode, {"amount": 0.0, "invoices": set()})
		data["amount"] += flt(row.amount)
		data["invoices"].add(row.parent)

	paid_total = sum(flt(invoice.paid_amount) for invoice in invoices)
	methods = []
	for mode, data in sorted(method_map.items(), key=lambda item: -item[1]["amount"]):
		percentage = round(data["amount"] / paid_total * 100, 1) if paid_total else 0
		methods.append(
			{
				"mode": mode,
				"amount": round(data["amount"], 2),
				"count": len(data["invoices"]),
				"percentage": percentage,
			}
		)
	return {
		"from_date": fd,
		"to_date": td,
		"methods": methods,
		"invoice_total": round(sum(flt(invoice.grand_total) for invoice in invoices), 2),
		"paid_total": round(paid_total, 2),
		"payment_rows_total": round(sum(flt(row.amount) for row in rows), 2),
		"outstanding_total": round(sum(max(flt(invoice.outstanding_amount), 0) for invoice in invoices), 2),
	}


@frappe.whitelist()
def get_recent_transactions(pos_profile, period="today", from_date=None, to_date=None, limit=20):
	_authorize(pos_profile)
	fd, td = _date_range(period, from_date, to_date)
	lim = max(1, min(cint(limit), 100))
	company = frappe.db.get_value("POS Profile", pos_profile, "company")
	invoices = frappe.get_all(
		"Sales Invoice",
		filters={
			"docstatus": 1,
			"is_pos": 1,
			"pos_profile": pos_profile,
			"company": company,
			"posting_date": ["between", [fd, td]],
		},
		fields=[
			"name", "customer", "customer_name", "grand_total", "net_total",
			"outstanding_amount", "is_return", "posting_date", "posting_time", "currency", "status",
		],
		order_by="posting_date desc, posting_time desc, name desc",
		limit=lim,
	)
	if invoices:
		payments = frappe.get_all(
			"Sales Invoice Payment",
			filters={"parent": ["in", [invoice.name for invoice in invoices]]},
			fields=["parent", "mode_of_payment", "amount"],
			order_by="amount desc",
			limit=0,
		)
		pay_map = {}
		for payment in payments:
			pay_map.setdefault(payment.parent, payment.mode_of_payment)
		for invoice in invoices:
			invoice.payment_method = pay_map.get(invoice.name, "")
			invoice.posting_datetime = str(
				get_datetime(f"{invoice.posting_date} {invoice.posting_time or '00:00:00'}")
			)
	return {"from_date": fd, "to_date": td, "transactions": list(invoices), "count": len(invoices)}


@frappe.whitelist()
def get_current_shift_profile():
	assert_report_manager()
	shift = frappe.get_all(
		"POS Opening Shift",
		filters={"user": frappe.session.user, "docstatus": 1, "status": "Open"},
		fields=["pos_profile"],
		order_by="period_start_date desc",
		limit=1,
	)
	if not shift:
		return {"pos_profile": None}
	profile = shift[0].pos_profile
	try:
		_authorize(profile)
	except frappe.PermissionError:
		return {"pos_profile": None}
	return {"pos_profile": profile}
