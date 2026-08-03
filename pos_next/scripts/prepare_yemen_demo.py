"""Prepare the Yemen POS demo with YER as its single reporting currency.

This is intentionally idempotent and safe to re-run after restoring the demo.
The exchange rates are illustrative demo rates, not live market data.
"""

import frappe
from frappe.utils import today


DEMO_RATES = {
    ("YER", "SAR"): 0.015,  # 1 SAR ~= 66.67 YER
    ("SAR", "YER"): 66.67,
    ("YER", "USD"): 0.004,  # 1 USD = 250 YER
    ("USD", "YER"): 250.0,
    ("YER", "EUR"): 0.0037,  # 1 EUR ~= 270.27 YER
    ("EUR", "YER"): 270.27,
}


def _set_if_field(doctype, name, fieldname, value):
    if frappe.get_meta(doctype).has_field(fieldname):
        frappe.db.set_value(doctype, name, fieldname, value, update_modified=False)
        return True
    return False


def _upsert_exchange_rate(rate_date, from_currency, to_currency, rate):
    filters = {
        "date": rate_date,
        "from_currency": from_currency,
        "to_currency": to_currency,
    }
    existing = frappe.get_all("Currency Exchange", filters=filters, fields=["name"], limit_page_length=1)
    if existing:
        frappe.db.set_value(
            "Currency Exchange",
            existing[0].name,
            {"exchange_rate": rate, "for_buying": 1, "for_selling": 1},
            update_modified=False,
        )
        return existing[0].name

    doc = frappe.get_doc(
        {
            "doctype": "Currency Exchange",
            "date": rate_date,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "exchange_rate": rate,
            "for_buying": 1,
            "for_selling": 1,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _find_fallback_account(company):
    accounts = frappe.get_all(
        "Account",
        filters={
            "company": company,
            "is_group": 0,
            "disabled": 0,
            "account_currency": "YER",
        },
        fields=["name", "account_type"],
        order_by="account_type desc, name asc",
        limit_page_length=100,
    )
    for account in accounts:
        if account.account_type in ("Cash", "Bank"):
            return account.name
    return accounts[0].name if accounts else None


def _repair_payment_accounts():
    repaired = []
    missing = []
    rows = frappe.get_all(
        "Mode of Payment Account",
        fields=["name", "parent", "company", "default_account"],
        limit_page_length=0,
    )
    for row in rows:
        account = frappe.db.get_value(
            "Account", row.default_account, ["account_currency", "company", "is_group", "disabled"], as_dict=True
        )
        valid = account and account.account_currency == "YER" and account.company == row.company and not account.is_group and not account.disabled
        if valid:
            continue
        fallback = _find_fallback_account(row.company)
        if not fallback:
            missing.append({"mode_of_payment": row.parent, "company": row.company})
            continue
        frappe.db.set_value("Mode of Payment Account", row.name, "default_account", fallback, update_modified=False)
        repaired.append({"mode_of_payment": row.parent, "company": row.company, "account": fallback})
    return repaired, missing


def prepare_yemen_demo(rate_date=None):
    """Apply the Yemen demo configuration and return a concise audit summary."""
    rate_date = rate_date or today()
    companies = frappe.get_all("Company", fields=["name", "default_currency", "reporting_currency"])
    foreign = [c.name for c in companies if c.default_currency and c.default_currency != "YER"]
    if foreign:
        frappe.throw("Refusing to rewrite companies with non-YER default currency: " + ", ".join(foreign))

    for company in companies:
        _set_if_field("Company", company.name, "default_currency", "YER")
        _set_if_field("Company", company.name, "reporting_currency", "YER")
        _set_if_field("Company", company.name, "country", "Yemen")

    profile_fields = {f.fieldname for f in frappe.get_meta("POS Profile").fields}
    profiles = frappe.get_all("POS Profile", fields=["name", "currency"])
    for profile in profiles:
        if "currency" in profile_fields:
            frappe.db.set_value("POS Profile", profile.name, "currency", "YER", update_modified=False)
        if "country" in profile_fields:
            frappe.db.set_value("POS Profile", profile.name, "country", "Yemen", update_modified=False)

    price_lists = frappe.get_all("Price List", fields=["name"])
    for price_list in price_lists:
        frappe.db.set_value("Price List", price_list.name, "currency", "YER", update_modified=False)
    frappe.db.sql("UPDATE `tabItem Price` SET currency = 'YER' WHERE currency IS NULL OR currency <> 'YER'")

    accounts = frappe.get_all("Account", fields=["name", "account_currency"])
    non_yer_accounts = [a.name for a in accounts if a.account_currency and a.account_currency != "YER"]
    if non_yer_accounts:
        frappe.throw("Refusing to rewrite accounts with non-YER currency: " + ", ".join(non_yer_accounts[:20]))
    for account in accounts:
        if not account.account_currency:
            frappe.db.set_value("Account", account.name, "account_currency", "YER", update_modified=False)

    repaired_payment_accounts, missing_payment_accounts = _repair_payment_accounts()

    # All companies now report in YER, so historical reporting values are a 1:1
    # copy of their existing debit/credit values. Monetary source columns remain untouched.
    frappe.db.sql(
        """UPDATE `tabGL Entry`
        SET reporting_currency_exchange_rate = 1,
            debit_in_reporting_currency = debit,
            credit_in_reporting_currency = credit"""
    )
    if frappe.db.table_exists("Account Closing Balance"):
        frappe.db.sql(
            """UPDATE `tabAccount Closing Balance`
            SET reporting_currency_exchange_rate = 1,
                debit_in_reporting_currency = debit,
                credit_in_reporting_currency = credit"""
        )

    exchange_rates = []
    for (from_currency, to_currency), rate in DEMO_RATES.items():
        exchange_rates.append(
            _upsert_exchange_rate(rate_date, from_currency, to_currency, rate)
        )

    frappe.db.commit()
    frappe.clear_cache()
    return {
        "rate_date": rate_date,
        "companies": len(companies),
        "pos_profiles": len(profiles),
        "price_lists": len(price_lists),
        "accounts": len(accounts),
        "payment_accounts_repaired": len(repaired_payment_accounts),
        "payment_accounts_missing": missing_payment_accounts,
        "exchange_rates": len(exchange_rates),
        "historical_reporting_currency": "YER (1:1)",
    }
