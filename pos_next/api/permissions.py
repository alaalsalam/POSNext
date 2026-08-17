# Copyright (c) 2025, POS Next and contributors
# For license information, please see license.txt

import frappe

from pos_next.api.feature_flags import (
	FEATURE_DEFAULTS,
	_get_active_pos_profile,
	get_feature_flags,
)


def _resolve_ui_pos_profile(pos_profile=None):
	"""Resolve the POS Profile to read feature flags from for UI show/hide.

	The frontend sometimes asks for permissions before a shift/profile is active
	(and used to get a degraded, all-flags-off result, spuriously hiding Catalog /
	Reports). Fall back to the user's active shift profile, then to their assigned
	POS Profile, so a legitimate POS user always gets their own shop's flags. This
	is UI-only — actual operations are still gated per active profile by
	require_feature().
	"""
	if pos_profile:
		return pos_profile
	active = _get_active_pos_profile()
	if active:
		return active
	return frappe.db.get_value("POS Profile User", {"user": frappe.session.user}, "parent")


@frappe.whitelist()
def get_pos_permissions(pos_profile=None):
	"""
	Return a dict of what the current user can do in the POS app.
	The frontend uses this to show/hide buttons and menu items.
	"""
	user_roles = frappe.get_roles()
	feature_flags = FEATURE_DEFAULTS.copy()
	try:
		feature_flags = get_feature_flags(pos_profile=_resolve_ui_pos_profile(pos_profile))
	except frappe.PermissionError:
		pass

	# Helper: check a single perm without raising
	def can(doctype, ptype):
		return bool(frappe.has_permission(doctype, ptype))

	return {
		# ── Promotion management (POS Manager only) ──
		"can_read_promotions": can("Promotional Scheme", "read"),
		"can_create_promotions": can("Promotional Scheme", "create"),
		"can_write_promotions": can("Promotional Scheme", "write"),
		"can_delete_promotions": can("Promotional Scheme", "delete"),
		# ── Coupon management ──
		"can_read_coupons": can("POS Coupon", "read"),
		"can_create_coupons": can("POS Coupon", "create"),
		"can_write_coupons": can("POS Coupon", "write"),
		"can_delete_coupons": can("POS Coupon", "delete"),
		# ── Referral codes ──
		"can_read_referrals": can("Referral Code", "read"),
		"can_create_referrals": can("Referral Code", "create"),
		"can_write_referrals": can("Referral Code", "write"),
		# ── Customer management ──
		"can_create_customers": can("Customer", "create"),
		"can_write_customers": can("Customer", "write"),
		# ── Item/catalog management ──
		"can_create_items": bool(feature_flags["enable_catalog_management"] and can("Item", "create")),
		"can_write_items": bool(feature_flags["enable_catalog_management"] and can("Item", "write")),
		# ── POS Settings ──
		"can_write_pos_settings": can("POS Settings", "write"),
		"can_manage_feature_flags": can("POS Settings", "write"),
		# Logical UI labels derived from native permissions, not role names.
		"is_pos_manager": can("POS Settings", "write"),
		"is_cashier": bool(can("POS Opening Shift", "create") and not can("POS Settings", "write")),
		# ── Purchase management ──
		"can_read_purchases": bool(feature_flags["enable_purchases"] and can("Purchase Invoice", "read")),
		"can_create_purchases": bool(feature_flags["enable_purchases"] and can("Purchase Invoice", "create")),
		"can_write_purchases": bool(feature_flags["enable_purchases"] and can("Purchase Invoice", "write")),
		"can_submit_purchases": bool(feature_flags["enable_purchases"] and can("Purchase Invoice", "submit")),
		"can_cancel_purchases": bool(feature_flags["enable_purchases"] and can("Purchase Invoice", "cancel")),
		"can_read_suppliers": can("Supplier", "read"),
		"can_create_suppliers": can("Supplier", "create"),
		# ── Supplier payments ──
		"can_read_payment_entries": bool(feature_flags["enable_supplier_payments"] and can("Payment Entry", "read")),
		"can_create_payment_entries": bool(feature_flags["enable_supplier_payments"] and can("Payment Entry", "create")),
		"can_write_payment_entries": bool(feature_flags["enable_supplier_payments"] and can("Payment Entry", "write")),
		"can_submit_payment_entries": bool(feature_flags["enable_supplier_payments"] and can("Payment Entry", "submit")),
		"can_cancel_payment_entries": bool(feature_flags["enable_supplier_payments"] and can("Payment Entry", "cancel")),
		# ── Cash / expenses ──
		"can_manage_cash": bool(feature_flags["enable_cash_management"] and can("Journal Entry", "create") and can("Journal Entry", "read")),
		"can_manage_expense_types": bool(feature_flags["enable_expense_types"] and can("POS Expense Type", "write")),
		# Native Stock Reconciliation remains the accounting source of truth.
		"can_manage_inventory": bool(
			can("Stock Reconciliation", "read") and can("Stock Reconciliation", "create")
		),
		# ── Reports ──
		"can_view_reports": bool(
			feature_flags["enable_pos_reports"]
			and can("Sales Invoice", "read")
			and can("Sales Invoice", "report")
		),
		"feature_flags": feature_flags,
		"user_roles": user_roles,
	}
