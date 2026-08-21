"""Install the A4/PDF invoice format used by WhatsApp delivery."""

from pathlib import Path

import frappe
from frappe.modules.import_file import import_file_by_path


def execute():
	print_format_dir = Path(frappe.get_app_path("pos_next")) / "pos_next/print_format"
	for filename in (
		"pos_next_receipt/pos_next_receipt.json",
		"pos_whatsapp_invoice/pos_whatsapp_invoice.json",
	):
		import_file_by_path(str(print_format_dir / filename), force=True, ignore_version=True)
	frappe.clear_cache()
