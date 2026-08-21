# Copyright (c) 2024, POS Next and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _
from frappe.utils import cint


@frappe.whitelist()
def get_csrf_token():
	"""
	Get CSRF token for the current session.
	Only returns CSRF token if user is authenticated with a valid session.

	Security checks:
	- User must be authenticated (not Guest)
	- Session must be valid
	- User must be enabled
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.AuthenticationError)

	if not frappe.db.get_value("User", frappe.session.user, "enabled"):
		frappe.throw(_("User is disabled"), frappe.AuthenticationError)

	if not frappe.session.sid or frappe.session.sid == "Guest":
		frappe.throw(_("Invalid session"), frappe.AuthenticationError)

	csrf_token = frappe.sessions.get_csrf_token()

	if not csrf_token:
		frappe.throw(_("Failed to generate CSRF token"), frappe.ValidationError)

	return {"csrf_token": csrf_token, "session_id": frappe.session.sid}


def _parse_list_parameter(value, param_name="parameter"):
	"""
	Parse a list parameter that may come as JSON string or list.

	Args:
		value: Value to parse (string or list)
		param_name: Name of parameter for error messages

	Returns:
		list: Parsed list value
	"""
	if isinstance(value, str):
		try:
			value = value.strip()
			return json.loads(value) if value else []
		except json.JSONDecodeError as e:
			frappe.throw(_("Could not parse '{0}' as JSON: {1}").format(param_name, str(e)))

	if not isinstance(value, list):
		return []

	return value


@frappe.whitelist()
def check_user_company():
	"""Return the user's active company from Frappe's native defaults.

	``frappe.defaults.get_user_default`` validates a Company default against the
	user's Company User Permissions.  It is therefore safe to use as the shared
	company context for POS defaults instead of picking an arbitrary permission
	row when a user belongs to more than one company.
	"""
	company = frappe.defaults.get_user_default("Company")
	if company and frappe.db.exists("Company", company):
		return {"has_company": True, "company": company}

	# Users can also have a dedicated POS company profile field.
	# Prefer it as the active context when native defaults are missing.
	profile_company = None
	if frappe.db.has_column("User", "custom_pos_company"):
		profile_company = frappe.db.get_value("User", frappe.session.user, "custom_pos_company")
	if profile_company and frappe.db.exists("Company", profile_company):
		return {"has_company": True, "company": profile_company}

	# Older users can have Company User Permissions without a matching Default
	# Value yet. Prefer the permission marked default, otherwise choose a stable
	# assigned company; opening a POS shift will persist that verified company as
	# the native user default for subsequent requests.
	permission = frappe.get_all(
		"User Permission",
		filters={"user": frappe.session.user, "allow": "Company"},
		fields=["for_value"],
		order_by="is_default desc, creation asc",
		limit=1,
	)
	if permission and frappe.db.exists("Company", permission[0].for_value):
		return {"has_company": True, "company": permission[0].for_value}

	return {"has_company": False, "company": ""}


def get_wallet_payment_modes():
	"""
	Get list of Mode of Payment names that are marked as wallet payments.

	Returns:
		list: List of Mode of Payment names with is_wallet_payment=1
	"""
	return frappe.get_all("Mode of Payment", filters={"is_wallet_payment": 1}, pluck="name")


def is_wallet_payment_mode(mode_of_payment):
	"""
	Check if a Mode of Payment is a wallet payment.

	Args:
		mode_of_payment: Mode of Payment name

	Returns:
		bool: True if the mode is a wallet payment
	"""
	if not mode_of_payment:
		return False

	return cint(frappe.get_cached_value("Mode of Payment", mode_of_payment, "is_wallet_payment"))
