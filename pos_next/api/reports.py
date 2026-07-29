# Copyright (c) 2025, POS Next and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, nowdate, add_days, add_to_date, now_datetime


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _get_user_pos_profiles(user=None):
    """Return list of POS profile names the current user is allowed to access."""
    if not user:
        user = frappe.session.user
    profiles = frappe.get_all(
        "POS Profile User",
        filters={"user": user},
        fields=["parent"],
        limit=0,
    )
    names = [p.parent for p in profiles]
    # Also exclude disabled profiles
    if names:
        enabled = frappe.get_all(
            "POS Profile",
            filters={"name": ["in", names], "disabled": 0},
            fields=["name"],
            limit=0,
        )
        return [e.name for e in enabled]
    return []


def _assert_profile_access(pos_profile):
    """Raise PermissionError if current user cannot access the given POS profile."""
    allowed = _get_user_pos_profiles()
    if pos_profile not in allowed:
        frappe.throw(
            _("Access denied: you are not authorized to view data for POS Profile '{0}'").format(pos_profile),
            frappe.PermissionError,
        )


def _date_range(period, from_date=None, to_date=None):
    """Resolve a named period to (from_date, to_date) strings."""
    today = nowdate()
    if period == "today" or (not period and not from_date):
        return today, today
    if period == "yesterday":
        y = add_days(today, -1)
        return y, y
    if period == "this_week":
        from frappe.utils import get_first_day_of_week
        start = str(get_first_day_of_week(today))
        return start, today
    if period == "this_month":
        from frappe.utils import get_first_day
        start = str(get_first_day(today))
        return start, today
    if period == "custom" and from_date and to_date:
        return str(getdate(from_date)), str(getdate(to_date))
    # Fallback
    return today, today


def _get_invoice_names(pos_profile, from_date, to_date, include_returns=True):
    """Return submitted, non-cancelled Sales Invoice names for the given profile + date range."""
    company = frappe.db.get_value("POS Profile", pos_profile, "company")
    filters = {
        "docstatus": 1,
        "pos_profile": pos_profile,
        "company": company,
        "posting_date": ["between", [from_date, to_date]],
    }
    if not include_returns:
        filters["is_return"] = 0
    return frappe.get_all(
        "Sales Invoice",
        filters=filters,
        fields=["name", "grand_total", "net_total", "total_taxes_and_charges",
                "is_return", "posting_datetime", "posting_date", "customer",
                "outstanding_amount", "currency"],
        order_by="posting_datetime desc",
        limit=0,
    )


# ─── Public APIs ──────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_report_filters():
    """Return the POS profiles the current user may report on, plus date-period options."""
    frappe.has_permission("Sales Invoice", "read", throw=True)
    allowed = _get_user_pos_profiles()
    profiles = []
    if allowed:
        profiles = frappe.get_all(
            "POS Profile",
            filters={"name": ["in", allowed]},
            fields=["name", "company", "currency"],
            order_by="name asc",
        )
    return {
        "pos_profiles": profiles,
        "periods": [
            {"key": "today",      "label": _("اليوم")},
            {"key": "yesterday",  "label": _("أمس")},
            {"key": "this_week",  "label": _("هذا الأسبوع")},
            {"key": "this_month", "label": _("هذا الشهر")},
            {"key": "custom",     "label": _("نطاق مخصص")},
        ],
    }


@frappe.whitelist()
def get_daily_summary(pos_profile, period="today", from_date=None, to_date=None):
    """
    Return KPI summary for the given POS profile + date range.
    Only counts submitted (docstatus=1) Sales Invoices.
    """
    frappe.has_permission("Sales Invoice", "read", throw=True)
    _assert_profile_access(pos_profile)

    fd, td = _date_range(period, from_date, to_date)
    invoices = _get_invoice_names(pos_profile, fd, td, include_returns=True)

    sales_total = 0.0
    sales_count = 0
    returns_total = 0.0
    returns_count = 0
    outstanding_total = 0.0

    for inv in invoices:
        if inv.is_return:
            returns_total += flt(abs(inv.grand_total or 0))
            returns_count += 1
        else:
            sales_total += flt(inv.grand_total or 0)
            sales_count += 1
            outstanding_total += flt(inv.outstanding_amount or 0)

    net_sales = sales_total - returns_total
    avg_invoice = (sales_total / sales_count) if sales_count else 0.0

    return {
        "from_date": fd,
        "to_date": td,
        "pos_profile": pos_profile,
        "sales_total": round(sales_total, 2),
        "sales_count": sales_count,
        "avg_invoice": round(avg_invoice, 2),
        "returns_total": round(returns_total, 2),
        "returns_count": returns_count,
        "outstanding_total": round(outstanding_total, 2),
        "net_sales": round(net_sales, 2),
        "currency": frappe.db.get_value("POS Profile", pos_profile, "currency") or "SAR",
    }


@frappe.whitelist()
def get_payment_breakdown(pos_profile, period="today", from_date=None, to_date=None):
    """
    Return payment method breakdown for submitted, non-return Sales Invoices.
    """
    frappe.has_permission("Sales Invoice", "read", throw=True)
    _assert_profile_access(pos_profile)

    fd, td = _date_range(period, from_date, to_date)
    # Only non-return invoices for payment analysis
    invoices = _get_invoice_names(pos_profile, fd, td, include_returns=False)

    if not invoices:
        return {"from_date": fd, "to_date": td, "methods": [], "grand_total": 0.0}

    invoice_names = [inv.name for inv in invoices]
    grand_total = sum(flt(inv.grand_total) for inv in invoices)

    payment_rows = frappe.get_all(
        "Sales Invoice Payment",
        filters={"parent": ["in", invoice_names]},
        fields=["mode_of_payment", "amount"],
        limit=0,
    )

    # Aggregate by mode
    method_map = {}
    for row in payment_rows:
        mode = row.mode_of_payment or "غير محدد"
        if mode not in method_map:
            method_map[mode] = {"amount": 0.0, "count": 0}
        method_map[mode]["amount"] += flt(row.amount or 0)
        method_map[mode]["count"] += 1

    methods = []
    for mode, data in sorted(method_map.items(), key=lambda x: -x[1]["amount"]):
        pct = round((data["amount"] / grand_total * 100), 1) if grand_total else 0
        methods.append({
            "mode": mode,
            "amount": round(data["amount"], 2),
            "count": data["count"],
            "percentage": pct,
        })

    return {
        "from_date": fd,
        "to_date": td,
        "methods": methods,
        "grand_total": round(grand_total, 2),
    }


@frappe.whitelist()
def get_recent_transactions(pos_profile, period="today", from_date=None, to_date=None, limit=20):
    """Return the most recent Sales Invoices for the given profile + period."""
    frappe.has_permission("Sales Invoice", "read", throw=True)
    _assert_profile_access(pos_profile)

    fd, td = _date_range(period, from_date, to_date)
    lim = min(cint(limit), 100)  # cap at 100

    company = frappe.db.get_value("POS Profile", pos_profile, "company")
    invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "pos_profile": pos_profile,
            "company": company,
            "posting_date": ["between", [fd, td]],
        },
        fields=["name", "customer", "customer_name", "grand_total", "net_total",
                "outstanding_amount", "is_return", "posting_datetime",
                "posting_date", "currency", "status"],
        order_by="posting_datetime desc",
        limit=lim,
    )

    # Fetch primary payment method for each invoice in one batch
    if invoices:
        inv_names = [i.name for i in invoices]
        payments = frappe.get_all(
            "Sales Invoice Payment",
            filters={"parent": ["in", inv_names]},
            fields=["parent", "mode_of_payment", "amount"],
            order_by="amount desc",
            limit=0,
        )
        # Build map: invoice -> top payment method
        pay_map = {}
        for p in payments:
            if p.parent not in pay_map:
                pay_map[p.parent] = p.mode_of_payment

        for inv in invoices:
            inv["payment_method"] = pay_map.get(inv.name, "")

    return {
        "from_date": fd,
        "to_date": td,
        "transactions": list(invoices),
        "count": len(invoices),
    }


@frappe.whitelist()
def get_current_shift_profile():
    """Return the open shift's POS profile for the current user, if any."""
    shift = frappe.get_all(
        "POS Opening Shift",
        filters={"user": frappe.session.user, "docstatus": 1, "status": "Open"},
        fields=["pos_profile"],
        order_by="period_start_date desc",
        limit=1,
    )
    if shift:
        profile = shift[0].pos_profile
        # Validate not corrupted
        if profile and not all(c in "? " for c in profile):
            if frappe.db.get_value("POS Profile", profile, "disabled") == 0:
                return {"pos_profile": profile}
    return {"pos_profile": None}
