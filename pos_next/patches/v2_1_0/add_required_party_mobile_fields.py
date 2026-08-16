"""Add a required, top-level mobile field to POS customer and supplier forms."""

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Customer": [
				{
					"fieldname": "custom_pos_mobile_no",
					"label": "Mobile Number",
					"fieldtype": "Data",
					"options": "Phone",
					"insert_after": "customer_name",
					"reqd": 1,
					"description": "Required for customer communication and WhatsApp invoice delivery.",
				}
			],
			"Supplier": [
				{
					"fieldname": "custom_pos_mobile_no",
					"label": "Mobile Number",
					"fieldtype": "Data",
					"options": "Phone",
					"insert_after": "supplier_name",
					"reqd": 1,
					"description": "Required for supplier communication.",
				}
			],
		},
		update=True,
	)
