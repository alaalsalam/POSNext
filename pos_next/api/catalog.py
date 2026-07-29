import json

import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def check_catalog_permission():
	"""Return whether the current user can manage catalog items."""
	can_manage = frappe.has_permission("Item", "create")
	return {"can_manage": can_manage}


@frappe.whitelist()
def create_quick_item(
	item_name,
	item_group,
	price=0,
	buying_price=0,
	stock_uom="Nos",
	opening_qty=0,
	warehouse=None,
):
	"""Create a new Item with an optional standard selling price."""
	frappe.has_permission("Item", "create", throw=True)

	if not item_name:
		frappe.throw(_("Item Name is required"))
	if not item_group:
		frappe.throw(_("Item Group is required"))

	price = flt(price)
	opening_qty = flt(opening_qty)

	try:
		doc = frappe.get_doc(
			{
				"doctype": "Item",
				"item_name": item_name,
				"item_code": item_name,
				"item_group": item_group,
				"stock_uom": stock_uom,
				"is_sales_item": 1,
				"is_stock_item": 1 if opening_qty > 0 else 0,
			}
		)
		doc.insert(ignore_permissions=False)

		if price > 0:
			item_price = frappe.get_doc(
				{
					"doctype": "Item Price",
					"price_list": "Standard Selling",
					"selling": 1,
					"item_code": doc.name,
					"price_list_rate": price,
				}
			)
			item_price.insert(ignore_permissions=False)

		if buying_price and flt(buying_price) > 0:
			buying_price_doc = frappe.get_doc({
				"doctype": "Item Price",
				"price_list": "Standard Buying",
				"buying": 1,
				"selling": 0,
				"item_code": doc.name,
				"price_list_rate": flt(buying_price),
			})
			buying_price_doc.insert(ignore_permissions=False)

		return {
			"item_code": doc.name,
			"item_name": doc.item_name,
			"item_group": doc.item_group,
			"price": price,
		}

	except frappe.ValidationError:
		raise
	except Exception as e:
		error_doc = frappe.log_error(
			"error in catalog API: create_quick_item",
			json.dumps(
				{
					"user": frappe.session.user,
					"datetime": frappe.utils.now(),
					"item_name": item_name,
					"item_group": item_group,
					"price": price,
					"error": str(e),
				},
				default=str,
			),
		)
		frappe.throw(_("An error occurred. Error ID: {0}").format(error_doc.name))


@frappe.whitelist()
def create_item_group(group_name, parent_item_group="All Item Groups"):
	"""Create a new leaf-level Item Group."""
	frappe.has_permission("Item Group", "create", throw=True)

	if not group_name:
		frappe.throw(_("Group Name is required"))

	if frappe.db.exists("Item Group", group_name):
		frappe.throw(_("Item Group '{0}' already exists").format(group_name))

	parent = parent_item_group or "All Item Groups"

	try:
		doc = frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": group_name,
				"parent_item_group": parent,
				"is_group": 0,
			}
		)
		doc.insert(ignore_permissions=False)

		return {"name": doc.name, "parent": doc.parent_item_group}

	except frappe.ValidationError:
		raise
	except Exception as e:
		error_doc = frappe.log_error(
			"error in catalog API: create_item_group",
			json.dumps(
				{
					"user": frappe.session.user,
					"datetime": frappe.utils.now(),
					"group_name": group_name,
					"parent_item_group": parent,
					"error": str(e),
				},
				default=str,
			),
		)
		frappe.throw(_("An error occurred. Error ID: {0}").format(error_doc.name))


@frappe.whitelist()
def get_item_groups_for_select():
	"""Return a flat list of leaf item group names for use in select inputs."""
	groups = frappe.get_all(
		"Item Group",
		filters={"is_group": 0, "show_in_website": ["!=", 0]},
		fields=["name"],
		order_by="name",
		limit=100,
	)

	if not groups:
		groups = frappe.get_all(
			"Item Group",
			filters={"is_group": 0},
			fields=["name"],
			order_by="name",
			limit=100,
		)

	return [g.name for g in groups]


@frappe.whitelist()
def get_item_prices(item_code):
    """Return selling and buying prices for an item across standard price lists."""
    frappe.has_permission("Item Price", "read", throw=True)

    prices = frappe.get_all(
        "Item Price",
        filters={"item_code": item_code},
        fields=["price_list", "price_list_rate", "selling", "buying", "currency"],
        order_by="price_list asc",
    )

    selling_price = 0.0
    buying_price = 0.0
    selling_price_list = "Standard Selling"
    buying_price_list = "Standard Buying"

    for p in prices:
        if p.selling and not p.buying:
            selling_price = flt(p.price_list_rate)
            selling_price_list = p.price_list
        if p.buying and not p.selling:
            buying_price = flt(p.price_list_rate)
            buying_price_list = p.price_list

    return {
        "selling_price": selling_price,
        "buying_price": buying_price,
        "selling_price_list": selling_price_list,
        "buying_price_list": buying_price_list,
        "all_prices": prices,
    }


@frappe.whitelist()
def update_item_prices(item_code, selling_price=None, buying_price=None,
                        selling_price_list="Standard Selling", buying_price_list="Standard Buying"):
    """Upsert selling and/or buying Item Price records for an item."""
    frappe.has_permission("Item Price", "write", throw=True)

    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Item '{0}' not found").format(item_code))

    updated = []

    if selling_price is not None:
        _upsert_item_price(item_code, selling_price_list, flt(selling_price), selling=1, buying=0)
        updated.append("selling")

    if buying_price is not None:
        _upsert_item_price(item_code, buying_price_list, flt(buying_price), selling=0, buying=1)
        updated.append("buying")

    return {"item_code": item_code, "updated": updated}


def _upsert_item_price(item_code, price_list, rate, selling=0, buying=0):
    """Insert or update a single Item Price record."""
    existing = frappe.db.get_value(
        "Item Price",
        {"item_code": item_code, "price_list": price_list},
        "name",
    )
    if existing:
        frappe.db.set_value("Item Price", existing, "price_list_rate", rate)
    else:
        doc = frappe.get_doc({
            "doctype": "Item Price",
            "item_code": item_code,
            "price_list": price_list,
            "price_list_rate": rate,
            "selling": selling,
            "buying": buying,
        })
        doc.insert(ignore_permissions=False)
