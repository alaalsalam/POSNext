import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

# Warehouse.default_in_transit_warehouse is a self-referential Link (Warehouse -> Warehouse).
# When a cashier has a User Permission on Warehouse (each POS profile restricts its user to a
# single sales warehouse) AND apply_strict_user_permissions is on, that permission cascades onto
# this transit link. Because the field is empty on virtually every warehouse, strict mode then
# excludes EVERY warehouse from list queries — so the in-POS purchase "receiving warehouse"
# dropdown (get_warehouses) returned zero rows for every restricted user, blocking purchases.
# Core already ships parent_warehouse (the other self-link) with ignore_user_permissions for the
# same reason; this makes the transit link consistent. The intended restriction is preserved:
# the query then correctly narrows to the user's permitted warehouse via the name condition.
DOCTYPE = "Warehouse"
FIELDNAME = "default_in_transit_warehouse"
PROPERTY = "ignore_user_permissions"


def execute():
	if not frappe.get_meta(DOCTYPE).get_field(FIELDNAME):
		return
	current = frappe.db.get_value(
		"Property Setter",
		{"doc_type": DOCTYPE, "field_name": FIELDNAME, "property": PROPERTY},
		"value",
	)
	if current == "1":
		return
	make_property_setter(
		DOCTYPE,
		FIELDNAME,
		PROPERTY,
		1,
		"Check",
		validate_fields_for_doctype=False,
	)
