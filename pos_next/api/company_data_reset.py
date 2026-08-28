"""Controlled financial-data reset for POS demo companies.

This module deliberately uses ERPNext document cancellation/deletion instead
of SQL deletion.  Cancellation reverses stock and accounting effects before a
cancelled or draft document is removed, preserving ledger integrity.
"""

import frappe


PROTECTED_COMPANIES = {"spare parts"}

# Children/settlements precede their originating commercial documents.  The
# list is intentionally conservative: generated GL and Stock Ledger rows are
# never deleted directly; ERPNext manages them through document controllers.
RESET_ORDER = (
	"POS Closing Shift",
	"POS Opening Shift",
	"Payment Entry",
	"Journal Entry",
	"Sales Invoice",
	"Purchase Invoice",
	"Delivery Note",
	"Purchase Receipt",
	"Stock Reconciliation",
	"Stock Entry",
	"Sales Order",
	"Purchase Order",
	"Material Request",
	"Quotation",
	"Payment Request",
)


def _companies_to_reset(protected_companies=None):
	protected = set(protected_companies or PROTECTED_COMPANIES)
	return [
		company
		for company in frappe.get_all("Company", pluck="name", limit_page_length=0)
		if company not in protected
	]


def _company_document_types():
	return [doctype for doctype in RESET_ORDER if frappe.db.exists("DocType", doctype) and frappe.get_meta(doctype).has_field("company")]


def _document_names(doctype, companies, docstatus=None):
	filters = {"company": ["in", companies]}
	if docstatus is not None:
		filters["docstatus"] = docstatus
	return frappe.get_all(
		doctype,
		filters=filters,
		pluck="name",
		order_by="modified desc",
		limit_page_length=0,
	)


def reset_company_transactions(protected_companies=None, dry_run=True):
	"""Cancel and delete commercial operations outside protected companies.

	``dry_run`` is deliberately the default.  Execution returns a per-document
	report and does not delete any generated ledger rows directly.  If a document
	cannot be cancelled because a dependency still exists, it remains untouched
	and is reported rather than being bypassed with SQL.
	"""
	companies = _companies_to_reset(protected_companies)
	if not companies:
		return {"protected_companies": sorted(protected_companies or PROTECTED_COMPANIES), "companies": [], "summary": {}}

	report = {
		"protected_companies": sorted(protected_companies or PROTECTED_COMPANIES),
		"companies": companies,
		"dry_run": bool(dry_run),
		"summary": {},
		"failures": [],
	}
	doctypes = _company_document_types()
	for doctype in doctypes:
		report["summary"][doctype] = {
			"submitted": len(_document_names(doctype, companies, 1)),
			"draft_or_cancelled": len(_document_names(doctype, companies, ["in", [0, 2]])),
			"cancelled": 0,
			"deleted": 0,
		}

	if dry_run:
		return report

	frappe.flags.in_pos_next_company_reset = True
	try:
		for doctype in doctypes:
			for name in _document_names(doctype, companies, 1):
				try:
					frappe.get_doc(doctype, name).cancel()
					report["summary"][doctype]["cancelled"] += 1
				except Exception:
					report["failures"].append({"doctype": doctype, "name": name, "stage": "cancel", "error": frappe.get_traceback()})

		# Delete drafts and cancelled documents only. A record that failed to
		# cancel stays submitted and therefore cannot be silently removed.
		for doctype in doctypes:
			for name in _document_names(doctype, companies, ["in", [0, 2]]):
				try:
					frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
					report["summary"][doctype]["deleted"] += 1
				except Exception:
					report["failures"].append({"doctype": doctype, "name": name, "stage": "delete", "error": frappe.get_traceback()})
	finally:
		frappe.flags.in_pos_next_company_reset = False

	frappe.clear_cache()
	return report


def remaining_company_operations(protected_companies=None):
	"""Return remaining non-protected operations for post-reset verification."""
	companies = _companies_to_reset(protected_companies)
	return {
		doctype: len(_document_names(doctype, companies))
		for doctype in _company_document_types()
	}
