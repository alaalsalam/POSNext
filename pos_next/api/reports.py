# Copyright (c) 2025, POS Next and contributors
# For license information, please see license.txt

"""Manager-only, profile-scoped reporting APIs for the Digit POS dashboard."""

import frappe
from frappe import _
from frappe.utils import add_days, cint, date_diff, flt, get_datetime, getdate, nowdate

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
FINANCIAL_REPORTS = (
	"Gross Profit", "Profit and Loss Statement", "Sales Analytics", "Balance Sheet", "Cash Flow",
	"Trial Balance", "General Ledger", "Stock Balance", "Stock Ledger", "Accounts Receivable", "Accounts Payable",
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
			"rounded_total",
			"net_total",
			"total_taxes_and_charges",
			"rounding_adjustment",
			"is_return",
			"posting_date",
			"posting_time",
			"customer",
			"outstanding_amount",
			"paid_amount",
			"write_off_amount",
			"change_amount",
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
		"desk_reports": [{"name": name, "label": _(name)} for name in DESK_REPORTS]
		+ ([{"name": name, "label": _(name)} for name in FINANCIAL_REPORTS] if "POS Financial Reports" in frappe.get_roles() else []),
	}


def _core_totals(invoices):
	"""Headline KPIs for a set of invoices — shared by the current and previous windows."""
	sales = [invoice for invoice in invoices if not invoice.is_return]
	returns = [invoice for invoice in invoices if invoice.is_return]
	sales_total = sum(flt(invoice.grand_total) for invoice in sales)
	return {
		"sales_total": sales_total,
		"sales_count": len(sales),
		"avg_invoice": sales_total / len(sales) if sales else 0.0,
		"returns_total": sum(abs(flt(invoice.grand_total)) for invoice in returns),
		"returns_count": len(returns),
		"outstanding_total": sum(max(flt(invoice.outstanding_amount), 0) for invoice in sales),
		"net_sales": sum(flt(invoice.grand_total) for invoice in invoices),
		"net_total": sum(flt(invoice.net_total) for invoice in invoices),
		"tax_total": sum(flt(invoice.total_taxes_and_charges) for invoice in invoices),
		"rounding_total": sum(flt(invoice.rounding_adjustment) for invoice in invoices),
	}


def _pct_change(current, previous):
	"""Percent change vs the previous window; None when there is no baseline to compare against."""
	if not previous:
		return None
	return round((flt(current) - flt(previous)) / flt(previous) * 100, 1)


def _previous_window(fd, td):
	"""Same-length window immediately preceding [fd, td]."""
	length = date_diff(td, fd) + 1
	prev_td = add_days(fd, -1)
	return add_days(prev_td, -(length - 1)), prev_td


@frappe.whitelist()
def get_daily_summary(pos_profile, period="today", from_date=None, to_date=None):
	_authorize(pos_profile)
	fd, td = _date_range(period, from_date, to_date)
	cur = _core_totals(_get_invoice_names(pos_profile, fd, td))
	# ERPNext grand_total is pre-rounding; rounded_total is grand_total + rounding_adjustment.
	component_difference = cur["net_sales"] - cur["net_total"] - cur["tax_total"]

	prev_fd, prev_td = _previous_window(fd, td)
	prev = _core_totals(_get_invoice_names(pos_profile, prev_fd, prev_td))

	return {
		"from_date": fd,
		"to_date": td,
		"pos_profile": pos_profile,
		"sales_total": round(cur["sales_total"], 2),
		"sales_count": cur["sales_count"],
		"avg_invoice": round(cur["avg_invoice"], 2),
		"returns_total": round(cur["returns_total"], 2),
		"returns_count": cur["returns_count"],
		"outstanding_total": round(cur["outstanding_total"], 2),
		"net_sales": round(cur["net_sales"], 2),
		"net_total": round(cur["net_total"], 2),
		"tax_total": round(cur["tax_total"], 2),
		"rounding_adjustment": round(cur["rounding_total"], 2),
		"reconciliation_difference": round(component_difference, 2),
		"reconciled": abs(component_difference) < 0.01,
		"currency": frappe.db.get_value("POS Profile", pos_profile, "currency") or "SAR",
		# Period-over-period comparison (same-length preceding window) so the UI can show trends.
		"previous": {
			"from_date": prev_fd,
			"to_date": prev_td,
			"sales_total": round(prev["sales_total"], 2),
			"sales_count": prev["sales_count"],
			"avg_invoice": round(prev["avg_invoice"], 2),
			"returns_total": round(prev["returns_total"], 2),
		},
		"delta": {
			"sales_total": _pct_change(cur["sales_total"], prev["sales_total"]),
			"sales_count": _pct_change(cur["sales_count"], prev["sales_count"]),
			"avg_invoice": _pct_change(cur["avg_invoice"], prev["avg_invoice"]),
			"returns_total": _pct_change(cur["returns_total"], prev["returns_total"]),
		},
	}


@frappe.whitelist()
def get_payment_breakdown(pos_profile, period="today", from_date=None, to_date=None):
	_authorize(pos_profile)
	fd, td = _date_range(period, from_date, to_date)
	invoices = _get_invoice_names(pos_profile, fd, td, include_returns=True)
	if not invoices:
		return {
			"from_date": fd,
			"to_date": td,
			"methods": [],
			"received_total": 0.0,
			"refunded_total": 0.0,
			"tender_total": 0.0,
			"net_total": 0.0,
			"change_total": 0.0,
			"settlement_difference": 0.0,
			"tender_difference": 0.0,
			"settlement_reconciled": True,
			"tender_reconciled": True,
		}

	invoice_names = [invoice.name for invoice in invoices]
	invoice_map = {invoice.name: invoice for invoice in invoices}
	rows = frappe.get_all(
		"Sales Invoice Payment",
		filters={"parent": ["in", invoice_names], "parenttype": "Sales Invoice"},
		fields=["parent", "mode_of_payment", "amount"],
		limit=0,
	)
	method_map = {}
	for row in rows:
		mode = row.mode_of_payment or _("Unspecified")
		data = method_map.setdefault(
			mode,
			{
				"received": 0.0,
				"refunded": 0.0,
				"received_invoices": set(),
				"refunded_invoices": set(),
			},
		)
		movement = abs(flt(row.amount))
		if invoice_map[row.parent].is_return:
			data["refunded"] += movement
			data["refunded_invoices"].add(row.parent)
		else:
			data["received"] += movement
			data["received_invoices"].add(row.parent)

	received_total = sum(data["received"] for data in method_map.values())
	refunded_total = sum(data["refunded"] for data in method_map.values())
	net_tender_total = received_total - refunded_total
	gross_movement = received_total + refunded_total
	methods = []
	for mode, data in sorted(
		method_map.items(), key=lambda item: (-(item[1]["received"] + item[1]["refunded"]), item[0])
	):
		net = data["received"] - data["refunded"]
		percentage = (
			round((data["received"] + data["refunded"]) / gross_movement * 100, 1)
			if gross_movement
			else 0
		)
		methods.append(
			{
				"mode": mode,
				"received": round(data["received"], 2),
				"refunded": round(data["refunded"], 2),
				"net": round(net, 2),
				"amount": round(net, 2),
				"received_count": len(data["received_invoices"]),
				"refunded_count": len(data["refunded_invoices"]),
				"count": len(data["received_invoices"] | data["refunded_invoices"]),
				"percentage": percentage,
			}
		)

	signed_rounded_total = sum(
		flt(invoice.rounded_total)
		if invoice.rounded_total is not None
		else flt(invoice.grand_total) + flt(invoice.rounding_adjustment)
		for invoice in invoices
	)
	signed_paid_total = sum(flt(invoice.paid_amount) for invoice in invoices)
	signed_outstanding_total = sum(flt(invoice.outstanding_amount) for invoice in invoices)
	signed_write_off_total = sum(flt(invoice.write_off_amount) for invoice in invoices)
	change_total = sum(flt(invoice.change_amount) for invoice in invoices)
	settlement_difference = signed_rounded_total - (
		signed_paid_total + signed_outstanding_total + signed_write_off_total - change_total
	)
	tender_difference = net_tender_total - signed_paid_total
	net_movement_total = net_tender_total - change_total
	return {
		"from_date": fd,
		"to_date": td,
		"methods": methods,
		"invoice_total": round(sum(flt(invoice.grand_total) for invoice in invoices), 2),
		"rounded_total": round(signed_rounded_total, 2),
		"received_total": round(received_total, 2),
		"refunded_total": round(refunded_total, 2),
		"tender_total": round(net_tender_total, 2),
		"net_total": round(net_movement_total, 2),
		"paid_total": round(signed_paid_total, 2),
		"outstanding_total": round(signed_outstanding_total, 2),
		"write_off_total": round(signed_write_off_total, 2),
		"change_total": round(change_total, 2),
		"rounding_adjustment": round(sum(flt(invoice.rounding_adjustment) for invoice in invoices), 2),
		"settlement_difference": round(settlement_difference, 2),
		"tender_difference": round(tender_difference, 2),
		"settlement_reconciled": abs(settlement_difference) < 0.01,
		"tender_reconciled": abs(tender_difference) < 0.01,
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


@frappe.whitelist()
def get_sales_trend(pos_profile, period="today", from_date=None, to_date=None):
	"""Sales over time for the trend chart: hourly for a single day, daily otherwise."""
	_authorize(pos_profile)
	fd, td = _date_range(period, from_date, to_date)
	invoices = [inv for inv in _get_invoice_names(pos_profile, fd, td) if not inv.is_return]
	currency = frappe.db.get_value("POS Profile", pos_profile, "currency") or "SAR"

	if fd == td:
		buckets = {f"{hour:02d}": {"label": f"{hour:02d}:00", "sales": 0.0, "count": 0} for hour in range(24)}
		for inv in invoices:
			hour = get_datetime(f"{inv.posting_date} {inv.posting_time or '00:00:00'}").hour
			bucket = buckets[f"{hour:02d}"]
			bucket["sales"] += flt(inv.grand_total)
			bucket["count"] += 1
		ordered = list(buckets.values())
		granularity = "hour"
	else:
		ordered = []
		buckets = {}
		day = getdate(fd)
		end = getdate(td)
		while day <= end:
			key = str(day)
			bucket = {"label": key, "sales": 0.0, "count": 0}
			buckets[key] = bucket
			ordered.append(bucket)
			day = add_days(day, 1)
		for inv in invoices:
			bucket = buckets.get(str(getdate(inv.posting_date)))
			if bucket:
				bucket["sales"] += flt(inv.grand_total)
				bucket["count"] += 1
		granularity = "day"

	for bucket in ordered:
		bucket["sales"] = round(bucket["sales"], 2)
	return {"from_date": fd, "to_date": td, "granularity": granularity, "buckets": ordered, "currency": currency}


@frappe.whitelist()
def get_top_items(pos_profile, period="today", from_date=None, to_date=None, limit=10):
	"""Best-selling items (fast movers) by revenue over the period; returns excluded."""
	_authorize(pos_profile)
	fd, td = _date_range(period, from_date, to_date)
	lim = max(1, min(cint(limit), 50))
	currency = frappe.db.get_value("POS Profile", pos_profile, "currency") or "SAR"
	names = [inv.name for inv in _get_invoice_names(pos_profile, fd, td, include_returns=False)]
	if not names:
		return {"from_date": fd, "to_date": td, "items": [], "currency": currency}

	rows = frappe.get_all(
		"Sales Invoice Item",
		filters={"parent": ["in", names], "parenttype": "Sales Invoice"},
		fields=["item_code", "item_name", "qty", "amount", "stock_uom"],
		limit=0,
	)
	aggregated = {}
	for row in rows:
		entry = aggregated.setdefault(
			row.item_code,
			{"item_code": row.item_code, "item_name": row.item_name, "qty": 0.0, "amount": 0.0, "uom": row.stock_uom},
		)
		entry["qty"] += flt(row.qty)
		entry["amount"] += flt(row.amount)
	items = sorted(aggregated.values(), key=lambda entry: (-entry["amount"], -entry["qty"]))[:lim]
	for entry in items:
		entry["qty"] = round(entry["qty"], 2)
		entry["amount"] = round(entry["amount"], 2)
	return {"from_date": fd, "to_date": td, "items": items, "currency": currency}
