"""Keep POS contact input aligned with ERPNext's primary-contact fields."""

import frappe
from frappe import _


POS_MOBILE_FIELD = "custom_pos_mobile_no"


def sync_pos_mobile_no(doc, method=None):
	"""Copy the POS mobile input to the standard mobile field before validation.

	ERPNext stores the canonical phone number on the party's primary Contact and
	reflects it in ``mobile_no``.  The POS field is intentionally placed next to
	the party name so it is collected at creation time, while this hook preserves
	compatibility with ERPNext reports and WhatsApp integrations.
	"""
	mobile_no = (doc.get(POS_MOBILE_FIELD) or doc.get("mobile_no") or "").strip()
	if not mobile_no:
		return

	doc.set(POS_MOBILE_FIELD, mobile_no)
	doc.mobile_no = mobile_no


def require_mobile_no(mobile_no, party_label):
	"""Validate mobile input for POS API endpoints with a clear translated error."""
	if not (mobile_no or "").strip():
		frappe.throw(_("Mobile Number is required for {0}").format(_(party_label)))
