"""Add a POS serial/reference string field to Item for the classic item screen.

This is a plain reference/model string (as shown in the classic screen's grid), NOT
ERPNext per-unit Serial No tracking — enabling has_serial_no would force serial entry
on every sale and break the POS flow.
"""

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Item": [
				{
					"fieldname": "custom_pos_serial",
					"label": "POS Serial",
					"fieldtype": "Data",
					"insert_after": "item_name",
					"translatable": 0,
					"in_standard_filter": 1,
				}
			]
		}
	)
