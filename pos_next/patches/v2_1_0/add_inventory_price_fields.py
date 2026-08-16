"""Add optional POS buying/selling rates to the native reconciliation screen."""

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields({
		"Stock Reconciliation": [{
			"fieldname": "custom_pos_profile", "label": "POS Profile", "fieldtype": "Link",
			"options": "POS Profile", "insert_after": "company", "read_only": 1,
		}],
		"Stock Reconciliation Item": [
			{"fieldname": "custom_pos_buying_rate", "label": "Buying Rate", "fieldtype": "Currency", "insert_after": "valuation_rate", "in_list_view": 1},
			{"fieldname": "custom_pos_selling_rate", "label": "Selling Rate", "fieldtype": "Currency", "insert_after": "custom_pos_buying_rate", "in_list_view": 1},
		],
	}, update=True)
	# Reapply the shipped native permissions because the role patch is one-shot.
	from pos_next.patches.v2_1_0.native_pos_roles import execute as install_roles

	install_roles()
