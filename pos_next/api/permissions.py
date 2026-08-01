# Copyright (c) 2025, POS Next and contributors
# For license information, please see license.txt

import frappe

from pos_next.api.feature_flags import FEATURE_DEFAULTS, get_feature_flags, is_feature_manager
from pos_next.api.reporting_access import is_report_manager


@frappe.whitelist()
def get_pos_permissions(pos_profile=None):
	"""
	Return a dict of what the current user can do in the POS app.
	The frontend uses this to show/hide buttons and menu items.
	"""
	user_roles = frappe.get_roles()
	feature_flags = FEATURE_DEFAULTS.copy()
	try:
		feature_flags = get_feature_flags(pos_profile=pos_profile)
	except frappe.PermissionError:
		pass

	# Helper: check a single perm without raising
	def can(doctype, ptype):
		return bool(frappe.has_permission(doctype, ptype))

	can_manage_workflows = is_feature_manager()

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
		"can_create_items": bool(can_manage_workflows and feature_flags["enable_catalog_management"] and can("Item", "create")),
		"can_write_items": bool(can_manage_workflows and feature_flags["enable_catalog_management"] and can("Item", "write")),
		# ── POS Settings ──
		"can_write_pos_settings": can("POS Settings", "write"),
		"can_manage_feature_flags": is_feature_manager() and can("POS Settings", "write"),
		# ── Role shortcuts ──
		"is_pos_manager": "POS Manager" in user_roles or "System Manager" in user_roles,
		"is_cashier": "POSNext Cashier" in user_roles,
		# ── Purchase management ──
		"can_read_purchases": bool(can_manage_workflows and feature_flags["enable_purchases"] and can("Purchase Invoice", "read")),
		"can_create_purchases": bool(can_manage_workflows and feature_flags["enable_purchases"] and can("Purchase Invoice", "create")),
		"can_write_purchases": bool(can_manage_workflows and feature_flags["enable_purchases"] and can("Purchase Invoice", "write")),
		"can_submit_purchases": bool(can_manage_workflows and feature_flags["enable_purchases"] and can("Purchase Invoice", "submit")),
		"can_cancel_purchases": bool(can_manage_workflows and feature_flags["enable_purchases"] and can("Purchase Invoice", "cancel")),
		"can_read_suppliers": can("Supplier", "read"),
		"can_create_suppliers": can("Supplier", "create"),
		# ── Supplier payments ──
		"can_read_payment_entries": bool(can_manage_workflows and feature_flags["enable_supplier_payments"] and can("Payment Entry", "read")),
		"can_create_payment_entries": bool(can_manage_workflows and feature_flags["enable_supplier_payments"] and can("Payment Entry", "create")),
		"can_write_payment_entries": bool(can_manage_workflows and feature_flags["enable_supplier_payments"] and can("Payment Entry", "write")),
		"can_submit_payment_entries": bool(can_manage_workflows and feature_flags["enable_supplier_payments"] and can("Payment Entry", "submit")),
		"can_cancel_payment_entries": bool(can_manage_workflows and feature_flags["enable_supplier_payments"] and can("Payment Entry", "cancel")),
		# ── Reports ──
		"can_view_reports": bool(
			feature_flags["enable_pos_reports"]
			and is_report_manager()
			and can("Sales Invoice", "read")
		),
		"feature_flags": feature_flags,
		"user_roles": user_roles,
	}
