# Copyright (c) 2025, POS Next and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.utils import flt, cint, nowdate, getdate, add_days, now_datetime


AMOUNT_TOLERANCE = 0.005


def _get_payable_invoice(name):
    """Load and validate a submitted Purchase Invoice the user may pay."""
    frappe.has_permission("Purchase Invoice", "read", throw=True)
    doc = frappe.get_doc("Purchase Invoice", name)
    frappe.has_permission("Purchase Invoice", "read", doc=doc, throw=True)
    if doc.docstatus != 1:
        frappe.throw(_("Only submitted purchase invoices can be paid"))
    if flt(doc.outstanding_amount) <= AMOUNT_TOLERANCE:
        frappe.throw(_("This purchase invoice has no outstanding amount"))
    return doc


def _validate_payment_amount(amount, outstanding):
    amount = flt(amount)
    outstanding = flt(outstanding)
    if amount <= 0:
        frappe.throw(_("Payment amount must be greater than zero"))
    if amount > outstanding + AMOUNT_TOLERANCE:
        frappe.throw(
            _("Payment amount {0} exceeds the outstanding amount {1}").format(
                frappe.format_value(amount, {"fieldtype": "Currency"}),
                frappe.format_value(outstanding, {"fieldtype": "Currency"}),
            )
        )
    return amount


# ─── Suppliers ───────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_suppliers(search="", limit=30):
    """Return supplier list for autocomplete."""
    frappe.has_permission("Supplier", "read", throw=True)
    filters = {"disabled": 0}
    if search:
        return frappe.get_all(
            "Supplier",
            filters={"disabled": 0, "supplier_name": ["like", f"%{search}%"]},
            fields=["name", "supplier_name", "supplier_group"],
            order_by="supplier_name asc",
            limit=cint(limit),
        )
    return frappe.get_all(
        "Supplier",
        filters=filters,
        fields=["name", "supplier_name", "supplier_group"],
        order_by="supplier_name asc",
        limit=cint(limit),
    )


@frappe.whitelist()
def create_supplier(supplier_name, supplier_group="All Supplier Groups"):
    """Quick-create a supplier."""
    frappe.has_permission("Supplier", "create", throw=True)
    if not supplier_name:
        frappe.throw(_("Supplier name is required"))
    if frappe.db.exists("Supplier", supplier_name):
        frappe.throw(_("Supplier '{0}' already exists").format(supplier_name))
    doc = frappe.get_doc({
        "doctype": "Supplier",
        "supplier_name": supplier_name,
        "supplier_group": supplier_group or "All Supplier Groups",
        "supplier_type": "Company",
    })
    doc.insert(ignore_permissions=False)
    return {"name": doc.name, "supplier_name": doc.supplier_name}


# ─── Purchase Invoices ───────────────────────────────────────────────────────

@frappe.whitelist()
def get_purchase_invoices(supplier=None, status=None, from_date=None, to_date=None, search=None, limit=50, start=0):
    """Return paginated list of Purchase Invoices with filters."""
    frappe.has_permission("Purchase Invoice", "read", throw=True)

    filters = {}
    if supplier:
        filters["supplier"] = supplier
    if status:
        filters["status"] = status
    if from_date:
        filters["posting_date"] = [">=", getdate(from_date)]
    if to_date:
        existing = filters.get("posting_date")
        if existing:
            filters["posting_date"] = ["between", [getdate(from_date), getdate(to_date)]]
        else:
            filters["posting_date"] = ["<=", getdate(to_date)]
    if search:
        filters["name"] = ["like", f"%{search}%"]

    invoices = frappe.get_list(
        "Purchase Invoice",
        filters=filters,
        fields=["name", "supplier", "supplier_name", "posting_date", "due_date",
                "grand_total", "outstanding_amount", "status", "docstatus",
                "bill_no", "currency"],
        order_by="posting_date desc, name desc",
        limit=cint(limit),
        start=cint(start),
    )

    total_count = len(
        frappe.get_list("Purchase Invoice", filters=filters, pluck="name", limit=0)
    )
    return {"invoices": invoices, "total": total_count}


@frappe.whitelist()
def get_purchase_invoice(name):
    """Return a single Purchase Invoice with its items."""
    frappe.has_permission("Purchase Invoice", "read", throw=True)
    doc = frappe.get_doc("Purchase Invoice", name)
    frappe.has_permission("Purchase Invoice", "read", doc=doc, throw=True)
    result = doc.as_dict()
    return result


@frappe.whitelist()
def get_new_purchase_invoice_defaults(company=None):
    """Return sensible defaults for a new Purchase Invoice form."""
    frappe.has_permission("Purchase Invoice", "create", throw=True)
    if not company:
        company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")

    buying_price_list = frappe.db.get_value("Company", company, "default_buying_price_list") or "Standard Buying"
    expense_account = frappe.db.get_value("Company", company, "default_expense_account")
    stock_received_account = frappe.db.get_value("Company", company, "stock_received_but_not_billed")

    return {
        "company": company,
        "posting_date": nowdate(),
        "due_date": add_days(nowdate(), 30),
        "buying_price_list": buying_price_list,
        "currency": frappe.db.get_value("Company", company, "default_currency") or "SAR",
    }


@frappe.whitelist()
def save_purchase_invoice(data):
    """Save (insert or update) a Purchase Invoice draft. Returns the doc name."""
    frappe.has_permission("Purchase Invoice", "create", throw=True)

    if isinstance(data, str):
        data = json.loads(data)

    name = data.get("name")

    try:
        if name and frappe.db.exists("Purchase Invoice", name):
            # Update existing draft
            doc = frappe.get_doc("Purchase Invoice", name)
            if doc.docstatus != 0:
                frappe.throw(_("Cannot edit a submitted or cancelled invoice"))
            frappe.has_permission("Purchase Invoice", "write", doc=doc, throw=True)
            doc.update(data)
        else:
            # New document
            doc = frappe.get_doc({"doctype": "Purchase Invoice", **data})

        doc.flags.ignore_mandatory = False
        doc.save(ignore_permissions=False)
        return {"name": doc.name, "status": "Saved"}

    except frappe.ValidationError:
        raise
    except Exception as e:
        error_doc = frappe.log_error(
            "error in purchases API: save_purchase_invoice",
            json.dumps({"user": frappe.session.user, "datetime": str(now_datetime()), "data_name": name, "error": str(e)}, default=str),
        )
        frappe.throw(_("An error occurred. Error ID: {0}").format(error_doc.name))


@frappe.whitelist()
def submit_purchase_invoice(name):
    """Submit a Purchase Invoice (docstatus 0 → 1). Updates stock and accounts via ERPNext hooks."""
    frappe.has_permission("Purchase Invoice", "submit", throw=True)

    doc = frappe.get_doc("Purchase Invoice", name)
    if doc.docstatus != 0:
        frappe.throw(_("Invoice is not in Draft status"))
    frappe.has_permission("Purchase Invoice", "submit", doc=doc, throw=True)

    try:
        doc.submit()
        return {"name": doc.name, "status": "Submitted", "docstatus": doc.docstatus}
    except frappe.ValidationError:
        raise
    except Exception as e:
        error_doc = frappe.log_error(
            "error in purchases API: submit_purchase_invoice",
            json.dumps({"user": frappe.session.user, "datetime": str(now_datetime()), "name": name, "error": str(e)}, default=str),
        )
        frappe.throw(_("An error occurred. Error ID: {0}").format(error_doc.name))


@frappe.whitelist()
def cancel_purchase_invoice(name):
    """Cancel a submitted Purchase Invoice."""
    frappe.has_permission("Purchase Invoice", "cancel", throw=True)
    doc = frappe.get_doc("Purchase Invoice", name)
    if doc.docstatus != 1:
        frappe.throw(_("Invoice is not submitted"))
    frappe.has_permission("Purchase Invoice", "cancel", doc=doc, throw=True)
    try:
        doc.cancel()
        return {"name": doc.name, "status": "Cancelled"}
    except frappe.ValidationError:
        raise
    except Exception as e:
        error_doc = frappe.log_error(
            "error in purchases API: cancel_purchase_invoice",
            json.dumps({"user": frappe.session.user, "datetime": str(now_datetime()), "name": name, "error": str(e)}, default=str),
        )
        frappe.throw(_("An error occurred. Error ID: {0}").format(error_doc.name))


# ─── Items for Purchasing ────────────────────────────────────────────────────

@frappe.whitelist()
def get_purchase_items(search="", limit=30):
    """Return items for autocomplete in purchase invoice lines."""
    frappe.has_permission("Item", "read", throw=True)
    filters = {"disabled": 0, "is_purchase_item": 1}
    if search:
        filters["item_name"] = ["like", f"%{search}%"]

    items = frappe.get_all(
        "Item",
        filters=filters,
        fields=["name as item_code", "item_name", "stock_uom", "item_group"],
        order_by="item_name asc",
        limit=cint(limit),
    )

    if not items and search:
        # fallback: search by code too
        items = frappe.get_all(
            "Item",
            filters={"disabled": 0, "name": ["like", f"%{search}%"]},
            fields=["name as item_code", "item_name", "stock_uom", "item_group"],
            order_by="item_name asc",
            limit=cint(limit),
        )

    return items


@frappe.whitelist()
def get_item_buying_price(item_code, buying_price_list="Standard Buying"):
    """Return the buying price for an item from the given price list."""
    frappe.has_permission("Item Price", "read", throw=True)
    price = frappe.db.get_value(
        "Item Price",
        {"item_code": item_code, "price_list": buying_price_list, "buying": 1},
        "price_list_rate",
    )
    return {"item_code": item_code, "buying_price": flt(price), "price_list": buying_price_list}


@frappe.whitelist()
def get_warehouses(company=None):
    """Return non-group warehouses for the given company."""
    frappe.has_permission("Warehouse", "read", throw=True)
    filters = {"is_group": 0, "disabled": 0}
    if company:
        filters["company"] = company
    return frappe.get_all(
        "Warehouse",
        filters=filters,
        fields=["name", "warehouse_name", "company"],
        order_by="warehouse_name asc",
        limit=100,
    )


@frappe.whitelist()
def get_expense_accounts(company):
    """Return expense accounts for a company for use in purchase invoice line."""
    frappe.has_permission("Account", "read", throw=True)
    return frappe.get_all(
        "Account",
        filters={"company": company, "is_group": 0, "root_type": ["in", ["Expense", "Asset"]], "account_type": ["in", ["Stock", "Expense Account", "Fixed Asset", ""]]},
        fields=["name", "account_name", "account_type"],
        order_by="account_name asc",
        limit=50,
    )


# ─── Supplier Payments ──────────────────────────────────────────────────────

@frappe.whitelist()
def get_supplier_payment_defaults(invoice_name):
    """Return safe defaults and selectable cash/bank accounts for a supplier payment."""
    frappe.has_permission("Payment Entry", "create", throw=True)
    invoice = _get_payable_invoice(invoice_name)
    frappe.has_permission("Account", "read", throw=True)
    frappe.has_permission("Mode of Payment", "read", throw=True)

    accounts = frappe.get_list(
        "Account",
        filters={
            "company": invoice.company,
            "is_group": 0,
            "disabled": 0,
            "account_type": ["in", ["Cash", "Bank"]],
        },
        fields=["name", "account_name", "account_type", "account_currency"],
        order_by="account_type asc, account_name asc",
        limit=200,
    )
    modes = frappe.get_list(
        "Mode of Payment",
        fields=["name", "type"],
        order_by="name asc",
        limit=100,
    )
    mode_accounts = frappe.get_all(
        "Mode of Payment Account",
        filters={"company": invoice.company, "parent": ["in", [m.name for m in modes] or [""]]},
        fields=["parent", "default_account"],
        limit=0,
    )
    default_by_mode = {row.parent: row.default_account for row in mode_accounts}
    for mode in modes:
        mode["default_account"] = default_by_mode.get(mode.name)

    return {
        "invoice": {
            "name": invoice.name,
            "supplier": invoice.supplier,
            "supplier_name": invoice.supplier_name,
            "company": invoice.company,
            "currency": invoice.currency,
            "grand_total": flt(invoice.grand_total),
            "outstanding_amount": flt(invoice.outstanding_amount),
        },
        "posting_date": nowdate(),
        "accounts": accounts,
        "modes_of_payment": modes,
        "can_submit": bool(frappe.has_permission("Payment Entry", "submit")),
    }


@frappe.whitelist()
def create_supplier_payment(
    invoice_name,
    amount,
    posting_date=None,
    mode_of_payment=None,
    paid_from=None,
    reference_no=None,
    reference_date=None,
    remarks=None,
    submit=0,
):
    """Create a standard Payment Entry allocated to a Purchase Invoice."""
    frappe.has_permission("Payment Entry", "create", throw=True)
    invoice = _get_payable_invoice(invoice_name)
    amount = _validate_payment_amount(amount, invoice.outstanding_amount)
    submit = cint(submit)
    if submit:
        frappe.has_permission("Payment Entry", "submit", throw=True)

    if not paid_from:
        frappe.throw(_("Please select a cash or bank account"))
    account = frappe.get_doc("Account", paid_from)
    frappe.has_permission("Account", "read", doc=account, throw=True)
    if account.company != invoice.company or account.is_group or account.disabled:
        frappe.throw(_("The selected payment account is not valid for this company"))
    if account.account_type not in ("Cash", "Bank"):
        frappe.throw(_("The payment account must be a Cash or Bank account"))

    if mode_of_payment:
        frappe.has_permission("Mode of Payment", "read", throw=True)
        if not frappe.db.exists("Mode of Payment", mode_of_payment):
            frappe.throw(_("Invalid mode of payment"))

    posting_date = getdate(posting_date or nowdate())
    reference_date = getdate(reference_date or posting_date)

    try:
        from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

        payment = get_payment_entry(
            "Purchase Invoice",
            invoice.name,
            party_amount=amount,
            bank_account=paid_from,
            payment_type="Pay",
            reference_date=reference_date,
        )
        payment.posting_date = posting_date
        payment.reference_date = reference_date
        payment.mode_of_payment = mode_of_payment
        payment.reference_no = reference_no
        payment.remarks = remarks
        payment.paid_from = paid_from

        # Keep the allocation exact even when the invoice uses payment terms.
        remaining = amount
        for row in payment.references:
            allocation = min(flt(row.outstanding_amount), remaining)
            row.allocated_amount = allocation
            remaining -= allocation
        if remaining > AMOUNT_TOLERANCE:
            frappe.throw(_("Unable to allocate the full payment amount to the invoice"))

        payment.set_amounts()
        payment.insert(ignore_permissions=False)
        if submit:
            payment.submit()

        invoice.reload()
        return {
            "name": payment.name,
            "docstatus": payment.docstatus,
            "status": _("Submitted") if payment.docstatus == 1 else _("Draft"),
            "invoice": invoice.name,
            "outstanding_amount": flt(invoice.outstanding_amount),
            "invoice_status": invoice.status,
        }
    except frappe.ValidationError:
        raise
    except Exception as e:
        error_doc = frappe.log_error(
            "error in purchases API: create_supplier_payment",
            json.dumps(
                {
                    "user": frappe.session.user,
                    "datetime": str(now_datetime()),
                    "invoice": invoice_name,
                    "error": str(e),
                },
                default=str,
            ),
        )
        frappe.throw(_("Could not create the supplier payment. Error ID: {0}").format(error_doc.name))


@frappe.whitelist()
def get_supplier_payments(supplier=None, company=None, from_date=None, to_date=None, limit=50, start=0):
    """List supplier Payment Entries visible to the current user."""
    frappe.has_permission("Payment Entry", "read", throw=True)
    filters = {"party_type": "Supplier", "payment_type": "Pay"}
    if supplier:
        filters["party"] = supplier
    if company:
        filters["company"] = company
    if from_date and to_date:
        filters["posting_date"] = ["between", [getdate(from_date), getdate(to_date)]]
    elif from_date:
        filters["posting_date"] = [">=", getdate(from_date)]
    elif to_date:
        filters["posting_date"] = ["<=", getdate(to_date)]

    fields = [
        "name", "posting_date", "party", "party_name", "company", "paid_amount",
        "paid_from_account_currency", "mode_of_payment", "reference_no",
        "docstatus", "paid_from", "remarks",
    ]
    payments = frappe.get_list(
        "Payment Entry",
        filters=filters,
        fields=fields,
        order_by="posting_date desc, creation desc",
        limit=cint(limit),
        start=cint(start),
    )
    total = len(
        frappe.get_list("Payment Entry", filters=filters, pluck="name", limit=0)
    )
    return {"payments": payments, "total": total}


@frappe.whitelist()
def submit_supplier_payment(name):
    """Submit a supplier Payment Entry draft."""
    frappe.has_permission("Payment Entry", "submit", throw=True)
    payment = frappe.get_doc("Payment Entry", name)
    frappe.has_permission("Payment Entry", "submit", doc=payment, throw=True)
    if payment.party_type != "Supplier" or payment.payment_type != "Pay":
        frappe.throw(_("This payment is not a supplier payment"))
    if payment.docstatus != 0:
        frappe.throw(_("Only draft payments can be submitted"))
    payment.submit()
    return {"name": payment.name, "docstatus": payment.docstatus}


@frappe.whitelist()
def cancel_supplier_payment(name):
    """Cancel a submitted supplier Payment Entry."""
    frappe.has_permission("Payment Entry", "cancel", throw=True)
    payment = frappe.get_doc("Payment Entry", name)
    frappe.has_permission("Payment Entry", "cancel", doc=payment, throw=True)
    if payment.party_type != "Supplier" or payment.payment_type != "Pay":
        frappe.throw(_("This payment is not a supplier payment"))
    if payment.docstatus != 1:
        frappe.throw(_("Only submitted payments can be cancelled"))
    payment.cancel()
    return {"name": payment.name, "docstatus": payment.docstatus}


@frappe.whitelist()
def get_purchase_outstanding_summary(supplier=None, company=None, from_date=None, to_date=None):
    """Summarize submitted purchase invoices using permission-aware document queries."""
    frappe.has_permission("Purchase Invoice", "read", throw=True)
    filters = {"docstatus": 1}
    if supplier:
        filters["supplier"] = supplier
    if company:
        filters["company"] = company
    if from_date and to_date:
        filters["posting_date"] = ["between", [getdate(from_date), getdate(to_date)]]
    elif from_date:
        filters["posting_date"] = [">=", getdate(from_date)]
    elif to_date:
        filters["posting_date"] = ["<=", getdate(to_date)]

    rows = frappe.get_list(
        "Purchase Invoice",
        filters=filters,
        fields=["grand_total", "outstanding_amount", "status"],
        limit=0,
    )
    outstanding = sum(flt(row.outstanding_amount) for row in rows if flt(row.outstanding_amount) > 0)
    unpaid = sum(1 for row in rows if flt(row.outstanding_amount) >= flt(row.grand_total) - AMOUNT_TOLERANCE)
    partial = sum(
        1 for row in rows
        if AMOUNT_TOLERANCE < flt(row.outstanding_amount) < flt(row.grand_total) - AMOUNT_TOLERANCE
    )
    paid = sum(1 for row in rows if flt(row.outstanding_amount) <= AMOUNT_TOLERANCE)
    return {
        "total_outstanding": outstanding,
        "invoice_count": len(rows),
        "unpaid_count": unpaid,
        "partial_count": partial,
        "paid_count": paid,
    }
