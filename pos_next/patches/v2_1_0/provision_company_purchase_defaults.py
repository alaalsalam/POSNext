"""Provision isolated company masters and purchase defaults for existing profiles."""

from pos_next.api.pos_defaults import sync_multi_company_defaults


def execute():
	# Run even before the tenant switches to multi-company mode: every existing
	# profile then receives its own POS groups and safe default supplier. Once the
	# mode is enabled, the same idempotent routine attaches company ownership.
	from pos_next.api.pos_defaults import ensure_pos_profile_defaults
	import frappe

	for name in frappe.get_all("POS Profile", filters={"disabled": 0}, pluck="name", limit_page_length=0):
		ensure_pos_profile_defaults(frappe.get_doc("POS Profile", name))
	sync_multi_company_defaults()
