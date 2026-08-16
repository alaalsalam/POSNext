# Copyright (c) 2024, POS Next and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _
from frappe.utils import get_datetime, nowdate, nowtime

from pos_next.api.feature_flags import resolve_pos_profile
from pos_next.api.utilities import get_wallet_payment_modes


@frappe.whitelist()
def get_opening_dialog_data():
	"""Get data required for opening shift dialog"""
	data = {}

	# Get POS Profiles where current user is defined in POS Profile User table
	pos_profiles_data = frappe.db.sql(
		"""
		SELECT DISTINCT p.name, p.company, p.currency, p.warehouse, p.selling_price_list
		FROM `tabPOS Profile` p
		INNER JOIN `tabPOS Profile User` u ON u.parent = p.name
		WHERE p.disabled = 0 AND u.user = %s
		ORDER BY p.name
		""",
		frappe.session.user,
		as_dict=1,
	)

	data["pos_profiles_data"] = pos_profiles_data

	# Derive companies from accessible POS Profiles
	company_names = []
	for profile in pos_profiles_data:
		if profile.company and profile.company not in company_names:
			company_names.append(profile.company)
	data["companies"] = [{"name": c} for c in company_names]

	# Get payment methods for POS profiles (exclude wallet payment methods)
	pos_profiles_list = [p.name for p in pos_profiles_data]

	if pos_profiles_list:
		# Exclude wallet payment modes from opening balance
		wallet_modes = get_wallet_payment_modes()

		payment_filters = {"parent": ["in", pos_profiles_list]}
		if wallet_modes:
			payment_filters["mode_of_payment"] = ["not in", wallet_modes]

		data["payments_method"] = frappe.get_list(
			"POS Payment Method",
			filters=payment_filters,
			fields=["*"],
			limit_page_length=0,
			order_by="parent",
			ignore_permissions=True,
		)

		# Set currency from pos profile
		for mode in data["payments_method"]:
			mode["currency"] = frappe.get_cached_value("POS Profile", mode["parent"], "currency")
	else:
		data["payments_method"] = []

	return data


@frappe.whitelist()
def check_opening_shift(user=None):
	"""Check if user has an open shift"""
	if not user:
		user = frappe.session.user

	open_shifts = frappe.db.get_all(
		"POS Opening Shift",
		filters={
			"user": user,
			"pos_closing_shift": ["is", "not set"],
			"docstatus": 1,
			"status": "Open",
		},
		fields=["name", "pos_profile", "period_start_date"],
		order_by="period_start_date desc",
	)

	if not open_shifts:
		return None

	# Find the first shift with a valid, enabled POS Profile (skip corrupted/orphaned shifts)
	shift_data = None
	for candidate in open_shifts:
		profile_name = candidate.get("pos_profile") or ""
		# Corrupted names stored as "?" sequences — skip them
		if not profile_name or all(c in "? " for c in profile_name):
			continue
		# Skip if the profile no longer exists or has been disabled
		profile_disabled = frappe.db.get_value("POS Profile", profile_name, "disabled")
		if profile_disabled is None or profile_disabled:
			continue
		shift_data = candidate
		break

	if not shift_data:
		return None

	data = {}
	data["pos_opening_shift"] = frappe.get_doc("POS Opening Shift", shift_data["name"])
	data["pos_profile"] = frappe.get_doc("POS Profile", shift_data["pos_profile"])
	data["company"] = frappe.get_doc("Company", data["pos_profile"].company)
	# Include server timestamp so frontend can compute shift duration
	# without timezone mismatch (period_start_date is in server timezone)
	data["server_now"] = str(get_datetime())

	return data


@frappe.whitelist()
def create_opening_shift(pos_profile, company, balance_details):
	"""Create a new POS Opening Shift"""
	balance_details = json.loads(balance_details) if isinstance(balance_details, str) else balance_details

	# Check if user already has a valid open shift
	existing_shift = check_opening_shift(frappe.session.user)
	if existing_shift:
		shift_name = existing_shift["pos_opening_shift"].name
		profile_name = existing_shift.get("pos_profile", {}).name if hasattr(existing_shift.get("pos_profile", {}), "name") else str(existing_shift.get("pos_profile", ""))
		frappe.throw(
			_("يوجد لديك وردية مفتوحة بالفعل ({0}) — أغلقها أولاً ثم افتح وردية جديدة.").format(shift_name),
			title=_("وردية مفتوحة موجودة"),
		)

	# Never trust the profile or company received from the browser.  Native Frappe
	# Company User Permissions and the POS Profile User assignment are the single
	# source of truth for a cashier's company boundary.
	pos_profile = resolve_pos_profile(pos_profile=pos_profile, company=company)
	company = frappe.db.get_value("POS Profile", pos_profile, "company")

	# Opening-balance payment methods must be configured on the selected profile;
	# otherwise a crafted request could place balances from a different company.
	allowed_modes = set(
		frappe.get_all(
			"POS Payment Method",
			filters={"parent": pos_profile, "parenttype": "POS Profile"},
			pluck="mode_of_payment",
		)
	)
	for detail in balance_details or []:
		mode = detail.get("mode_of_payment")
		if mode not in allowed_modes:
			frappe.throw(_("Payment method {0} is not configured for this POS Profile").format(mode), frappe.PermissionError)

	new_pos_opening = frappe.get_doc(
		{
			"doctype": "POS Opening Shift",
			"period_start_date": get_datetime(),
			"posting_date": nowdate(),
			"posting_time": nowtime(),
			"user": frappe.session.user,
			"pos_profile": pos_profile,
			"company": company,
			"status": "Open",
		}
	)

	# Add balance details - map opening_amount to amount
	formatted_balance_details = []
	for detail in balance_details:
		formatted_balance_details.append(
			{"mode_of_payment": detail.get("mode_of_payment"), "amount": detail.get("opening_amount", 0)}
		)

	new_pos_opening.set("balance_details", formatted_balance_details)
	new_pos_opening.insert(ignore_permissions=True)
	new_pos_opening.submit()

	# Keep Frappe's native Company default aligned with the verified POS Profile.
	# Standard forms then prefill the same company, while User Permissions still
	# prevent selecting a company that has not been assigned to this user.
	frappe.defaults.set_user_default("Company", company)

	data = {}
	data["pos_opening_shift"] = new_pos_opening.as_dict()
	data["pos_profile"] = frappe.get_doc("POS Profile", pos_profile)
	data["company"] = frappe.get_doc("Company", company)

	return data


@frappe.whitelist()
def get_closing_shift_data(opening_shift):
	"""Get data for closing shift"""
	from pos_next.pos_next.doctype.pos_closing_shift.pos_closing_shift import make_closing_shift_from_opening

	try:
		# Get the opening shift document
		opening_shift_doc = frappe.get_doc("POS Opening Shift", opening_shift)

		# Convert to dict with proper datetime serialization
		opening_shift_dict = opening_shift_doc.as_dict()
		opening_shift_json = json.dumps(opening_shift_dict, default=str)

		# Create closing shift from opening shift (returns a dict)
		closing_data = make_closing_shift_from_opening(opening_shift_json)

		# Ensure datetime values are JSON serializable
		return json.loads(json.dumps(closing_data, default=str))
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Closing Shift Data Error")
		frappe.throw(_("Error getting closing shift data: {0}").format(str(e)))


@frappe.whitelist()
def submit_closing_shift(closing_shift):
	"""Submit closing shift"""
	from pos_next.pos_next.doctype.pos_closing_shift.pos_closing_shift import (
		submit_closing_shift as submit_shift,
	)

	try:
		# closing_shift is already a JSON string from frontend
		# If it's a dict, convert to JSON string
		if isinstance(closing_shift, dict):
			closing_shift = json.dumps(closing_shift)

		result = submit_shift(closing_shift)
		return {"name": result, "status": "success"}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Submit Closing Shift Error")
		frappe.throw(_("Error submitting closing shift: {0}").format(str(e)))


@frappe.whitelist()
def post_cash_variance(closing_shift):
	"""Post a closed shift's cash shortage/surplus to accounting, if within the configured cap."""
	from pos_next.pos_next.doctype.pos_closing_shift.pos_closing_shift import (
		post_cash_variance as post_variance,
	)

	return post_variance(closing_shift)


@frappe.whitelist()
def get_shift_stats(opening_shift):
	"""Return live stats for an open shift: invoice count, net sales, returns, payment totals."""
	frappe.has_permission("POS Opening Shift", "read", throw=True)

	shift = frappe.get_cached_doc("POS Opening Shift", opening_shift)
	if shift.user != frappe.session.user:
		frappe.has_permission("POS Opening Shift", "read", doc=shift, throw=True)

	# Fetch all submitted invoices for this shift in one query
	invoices = frappe.get_all(
		"Sales Invoice",
		filters={
			"posa_pos_opening_shift": opening_shift,
			"docstatus": 1,
		},
		fields=["name", "grand_total", "net_total", "total_taxes_and_charges", "is_return", "posting_date", "posting_time"],
		order_by="posting_date desc, posting_time desc",
	)

	sales_total = 0.0
	sales_count = 0
	returns_total = 0.0
	returns_count = 0
	last_invoice_time = None

	for inv in invoices:
		if not last_invoice_time and inv.posting_date:
			last_invoice_time = str(get_datetime(f"{inv.posting_date} {inv.posting_time or '00:00:00'}"))
		if inv.is_return:
			returns_total += abs(inv.grand_total or 0)
			returns_count += 1
		else:
			sales_total += inv.grand_total or 0
			sales_count += 1

	net_total = sales_total - returns_total

	# Aggregate payment totals — one query for all invoice names
	invoice_names = [inv.name for inv in invoices]
	payment_rows = []
	if invoice_names:
		payment_rows = frappe.get_all(
			"Sales Invoice Payment",
			filters={"parent": ["in", invoice_names]},
			fields=["mode_of_payment", "amount"],
		)

	payment_totals = {}
	for row in payment_rows:
		mode = row.mode_of_payment
		payment_totals[mode] = payment_totals.get(mode, 0.0) + (row.amount or 0)

	return {
		"sales_count": sales_count,
		"returns_count": returns_count,
		"sales_total": sales_total,
		"returns_total": returns_total,
		"net_total": net_total,
		"payment_totals": payment_totals,
		"last_invoice_time": last_invoice_time,
	}
