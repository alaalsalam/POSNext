"""Add explicit company ownership fields for POS master data."""

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Item": [{"fieldname": "custom_pos_company", "label": "POS Company", "fieldtype": "Link", "options": "Company", "insert_after": "item_name", "in_standard_filter": 1}],
			"Item Group": [{"fieldname": "custom_pos_company", "label": "POS Company", "fieldtype": "Link", "options": "Company", "insert_after": "item_group_name", "in_standard_filter": 1}],
			"Brand": [{"fieldname": "custom_pos_company", "label": "POS Company", "fieldtype": "Link", "options": "Company", "insert_after": "brand", "in_standard_filter": 1}],
			"Customer": [{"fieldname": "custom_pos_company", "label": "POS Company", "fieldtype": "Link", "options": "Company", "insert_after": "customer_name", "in_standard_filter": 1}],
			"Customer Group": [{"fieldname": "custom_pos_company", "label": "POS Company", "fieldtype": "Link", "options": "Company", "insert_after": "customer_group_name", "in_standard_filter": 1}],
			"Supplier": [{"fieldname": "custom_pos_company", "label": "POS Company", "fieldtype": "Link", "options": "Company", "insert_after": "supplier_name", "in_standard_filter": 1}],
			"Supplier Group": [{"fieldname": "custom_pos_company", "label": "POS Company", "fieldtype": "Link", "options": "Company", "insert_after": "supplier_group_name", "in_standard_filter": 1}],
			"User": [{"fieldname": "custom_pos_company", "label": "POS Company", "fieldtype": "Link", "options": "Company", "insert_after": "full_name", "in_standard_filter": 1}],
		},
		update=True,
	)
