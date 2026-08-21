"""Compact, permission-scoped KPIs for the POS Desk workspace."""

from __future__ import annotations

import frappe
from frappe.utils import flt, get_first_day, nowdate

from pos_next.api.reporting_access import assert_report_manager, get_reportable_profiles


@frappe.whitelist()
def get_workspace_overview():
	"""Return an account overview limited to the POS profiles the user may report on.

	This is deliberately separate from the operational POS screen: cashiers retain
	their regular selling access, while account-level totals require the same native
	report permission used by the POS reports.
	"""
	assert_report_manager()
	profiles = get_reportable_profiles()
	profile_names = [row.name for row in profiles]
	if not profile_names:
		return _empty_overview()

	today = nowdate()
	month_start = get_first_day(today)
	base_filters = {"docstatus": 1, "is_pos": 1, "pos_profile": ["in", profile_names]}
	today_invoices = frappe.get_all(
		"Sales Invoice",
		filters={**base_filters, "posting_date": today},
		fields=["name", "customer_name", "grand_total", "currency", "is_return", "posting_time"],
		order_by="posting_time desc, name desc",
		limit=0,
	)
	month_invoices = frappe.get_all(
		"Sales Invoice",
		filters={**base_filters, "posting_date": ["between", [month_start, today]]},
		fields=["grand_total", "is_return"],
		limit=0,
	)
	open_shifts = frappe.db.count(
		"POS Opening Shift", {"pos_profile": ["in", profile_names], "status": "Open"}
	)

	regular_today = [row for row in today_invoices if not row.is_return]
	returns_today = [row for row in today_invoices if row.is_return]
	regular_month = [row for row in month_invoices if not row.is_return]
	returns_month = [row for row in month_invoices if row.is_return]
	return {
		"can_view": 1,
		"today": str(today),
		"currency": _currency(profiles),
		"profile_count": len(profile_names),
		"company_count": len({row.company for row in profiles if row.company}),
		"today_sales": round(sum(flt(row.grand_total) for row in regular_today), 2),
		"today_invoices": len(regular_today),
		"today_returns": round(sum(abs(flt(row.grand_total)) for row in returns_today), 2),
		"month_sales": round(sum(flt(row.grand_total) for row in regular_month) - sum(abs(flt(row.grand_total)) for row in returns_month), 2),
		"open_shifts": open_shifts,
		"recent_invoices": [
			{
				"name": row.name,
				"customer_name": row.customer_name or "—",
				"grand_total": abs(flt(row.grand_total)),
				"is_return": bool(row.is_return),
			}
			for row in today_invoices[:5]
		],
	}


def _currency(profiles):
	currencies = {row.currency for row in profiles if row.currency}
	return next(iter(currencies)) if len(currencies) == 1 else ""


def _empty_overview():
	return {
		"can_view": 1,
		"today": str(nowdate()),
		"currency": "",
		"profile_count": 0,
		"company_count": 0,
		"today_sales": 0,
		"today_invoices": 0,
		"today_returns": 0,
		"month_sales": 0,
		"open_shifts": 0,
		"recent_invoices": [],
	}
