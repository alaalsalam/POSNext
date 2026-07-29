"""
Fix all POS demo issues:
1. Create VAT 15% account + template for every company that lacks one
2. Assign correct VAT template to every active POS profile
3. Remove duplicate Mada payment method from الأجهزة الكهربائية
4. Delete stale Draft opening shifts
"""
import frappe
from frappe.utils import now_datetime


# --- Config -----------------------------------------------------------

# All active POS profiles and their companies (from DB query)
PROFILES = [
    ("الآيس كريم",          "Ice Cream",                   "IC"),
    ("الأجهزة الكهربائية",  "Trilogy Electrical Appliances","TEA"),
    ("الألعاب",             "Toys.Trilogy",                 "Ty"),
    ("البيتزا",             "Pizza",                        "Pi"),
    ("الجوالات",            "Phones.Trilogy",               "Ph"),
    ("الذهب والمجوهرات",    "Gold and Jewelry",             "GJ"),
    ("الزهور",              "Fowers.Trilogy",               "F"),
    ("السوبر ماركت",        "Super Market",                 "SM"),
    ("الشوكولاتة",          "Chocolates.Trilogy",           "Ch"),
    ("الصيدلية",            "Pharmacy.Trilogy",             "P"),
    ("العطور",              "Perfumes.Trilogy",             "Per"),
    ("الكافيه",             "Cafe",                        "PD"),
    ("المطعم",              "Restaurant.Trilogy",           "R"),
    ("النظارات",            "Glasses.Trilogy",              "G"),
    ("صالون الحلاقة",       "Hairdressing.Trilogy",         "H"),
]

# Super Market already has a working template — use as reference
SM_TEMPLATE = "ضريبة القيمة المضافة 15% - SM - SM"


def ensure_vat_account(company, abbr):
    """Create the VAT liability account under Duties and Taxes if missing."""
    account_name = f"ضريبة القيمة المضافة 15% - {abbr}"
    if frappe.db.exists("Account", account_name):
        print(f"  Account already exists: {account_name}")
        return account_name

    parent = f"Duties and Taxes - {abbr}"
    if not frappe.db.exists("Account", parent):
        print(f"  ⚠️  No Duties and Taxes account for {company} — skipping")
        return None

    doc = frappe.get_doc({
        "doctype": "Account",
        "account_name": f"ضريبة القيمة المضافة 15%",
        "parent_account": parent,
        "company": company,
        "account_type": "Tax",
        "root_type": "Liability",
        "is_group": 0,
        "report_type": "Balance Sheet",
    })
    doc.insert(ignore_permissions=True)
    print(f"  ✅ Created account: {doc.name}")
    return doc.name


def ensure_vat_template(company, abbr, vat_account):
    """Create a 15% VAT Sales Tax template if the company doesn't have one."""
    template_name = f"ضريبة القيمة المضافة 15% - {abbr} - {abbr}"

    if frappe.db.exists("Sales Taxes and Charges Template", template_name):
        print(f"  Template already exists: {template_name}")
        return template_name

    doc = frappe.get_doc({
        "doctype": "Sales Taxes and Charges Template",
        "title": f"ضريبة القيمة المضافة 15% - {abbr}",
        "company": company,
        "is_default": 0,
        "disabled": 0,
        "taxes": [{
            "doctype": "Sales Taxes and Charges",
            "charge_type": "On Net Total",
            "account_head": vat_account,
            "rate": 15,
            "description": "ضريبة القيمة المضافة 15٪ — KSA VAT",
        }],
    })
    doc.insert(ignore_permissions=True)
    print(f"  ✅ Created template: {doc.name}")
    return doc.name


def assign_template_to_profile(profile_name, template_name):
    """Set taxes_and_charges on the POS Profile."""
    current = frappe.db.get_value("POS Profile", profile_name, "taxes_and_charges")
    if current == template_name:
        print(f"  Profile {profile_name} already has the correct template")
        return
    frappe.db.set_value("POS Profile", profile_name, "taxes_and_charges", template_name)
    print(f"  ✅ Assigned {template_name} → {profile_name}")


def fix_duplicate_mada():
    """Remove the duplicate 'مدي' (typo of مدى) from الأجهزة الكهربائية."""
    # Check both variants
    rows = frappe.db.get_all(
        "POS Payment Method",
        filters={"parent": "الأجهزة الكهربائية", "mode_of_payment": ["in", ["مدي", "مدى"]]},
        fields=["name", "mode_of_payment", "idx"],
        order_by="idx asc",
    )
    if len(rows) <= 1:
        print("  No duplicate Mada found")
        return
    # Keep the first, delete the rest
    for row in rows[1:]:
        frappe.delete_doc("POS Payment Method", row.name, ignore_permissions=True)
        print(f"  ✅ Removed duplicate payment method '{row.mode_of_payment}' (idx={row.idx})")


def delete_draft_shifts():
    """Delete stale Draft POS Opening Shifts (docstatus=0)."""
    drafts = frappe.db.get_all(
        "POS Opening Shift",
        filters={"docstatus": 0},
        fields=["name", "user", "pos_profile"],
    )
    for d in drafts:
        frappe.delete_doc("POS Opening Shift", d.name, ignore_permissions=True)
        print(f"  ✅ Deleted draft shift {d.name} ({d.user} / {d.pos_profile})")
    if not drafts:
        print("  No draft shifts found")


def run():
    print("\n=== Step 1: Create VAT accounts + templates for all companies ===")
    for profile_name, company, abbr in PROFILES:
        print(f"\n[{company}]")
        # Super Market already has its own template
        if company == "Super Market":
            current = frappe.db.get_value("POS Profile", profile_name, "taxes_and_charges")
            if current:
                print(f"  Super Market already has template: {current}")
                continue
            assign_template_to_profile(profile_name, SM_TEMPLATE)
            continue

        vat_account = ensure_vat_account(company, abbr)
        if not vat_account:
            continue
        template_name = ensure_vat_template(company, abbr, vat_account)
        assign_template_to_profile(profile_name, template_name)

    print("\n=== Step 2: Fix duplicate Mada payment method ===")
    fix_duplicate_mada()

    print("\n=== Step 3: Delete stale Draft opening shifts ===")
    delete_draft_shifts()

    frappe.db.commit()
    print("\n✅ All done.")
