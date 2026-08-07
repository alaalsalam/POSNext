import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

# Strict-user-permission false negatives in the in-POS purchase flow.
#
# This site runs with apply_strict_user_permissions on, and each POS profile pins its cashier
# to their company (Company User Permission) and sales warehouse (Warehouse User Permission) so
# a cashier only ever touches their own tenant's items/stock. Frappe's strict mode then requires
# EVERY non-ignored Link->Company / Link->Warehouse field on any per-document permission check
# (has_permission(doc=...), including child rows) to hold an allowed value — an EMPTY field fails
# (`str(None)` is never in the allowed set). Purchase creation does per-doc checks on the Item
# (assert_doc_permission) and on the Purchase Invoice (create + submit), and these documents carry
# metadata Company/Warehouse links that are empty in the normal flow, so restricted cashiers were
# blocked from adding a purchase item / submitting the invoice.
#
# We only relax fields that are metadata / defaults / inter-company markers and are NOT the real
# tenant boundary. The boundaries stay UP-checked: Item.company (multi-tenant item scoping),
# Purchase Invoice.company, Purchase Invoice.set_warehouse, Purchase Invoice Item.warehouse — all
# populated with the cashier's own company/warehouse in this flow. Company ownership is also still
# enforced by assert_company_resource and ERPNext's own validation, so these setters remove the
# false negative without weakening isolation.
#
# (Warehouse.default_in_transit_warehouse — the sibling case behind the empty receiving-warehouse
# dropdown — ships in warehouse_transit_ignore_user_perms.py.)
FIELDS = [
	("Item Default", "default_warehouse"),
	("Item Reorder", "warehouse"),
	("Item Reorder", "warehouse_group"),
	("Purchase Invoice", "represents_company"),
]
PROPERTY = "ignore_user_permissions"


def execute():
	for doctype, fieldname in FIELDS:
		if not frappe.get_meta(doctype).get_field(fieldname):
			continue
		current = frappe.db.get_value(
			"Property Setter",
			{"doc_type": doctype, "field_name": fieldname, "property": PROPERTY},
			"value",
		)
		if current == "1":
			continue
		make_property_setter(
			doctype,
			fieldname,
			PROPERTY,
			1,
			"Check",
			validate_fields_for_doctype=False,
		)
