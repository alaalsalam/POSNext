"""Add EAN-13 barcodes to all supermarket items."""
import frappe


def ean13_checkdigit(digits_12):
    s = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits_12))
    return (10 - (s % 10)) % 10


def make_ean13(prefix_7, seq):
    body = prefix_7 + str(seq).zfill(5)  # 7 + 5 = 12 digits
    return body + str(ean13_checkdigit(body))


CATEGORY_MANUFACTURERS = {
    "الجبنة القابلة للدهن (الكاسات)": "6280101",
    "الخبز":                            "6280202",
    "الزبادي والحلويات":               "6280303",
    "السويس رول":                       "6280404",
    "الفطائر":                          "6280505",
    "الكب كيك":                         "6280606",
    "اللبن الطازج":                     "6280707",
    "فارمز سيلكت":                      "6280808",
    "الكروسان سفن دايز":               "6280909",
    "الكرواسان":                        "6280910",
    "الكرواسان المحشو":                 "6280911",
}


def run():
    # Get all supermarket items via Bin table
    rows = frappe.db.sql("""
        SELECT DISTINCT i.name, i.item_name, i.item_group
        FROM `tabItem` i
        INNER JOIN `tabBin` b ON b.item_code = i.name
        WHERE b.warehouse = 'Finished Goods - SM'
          AND i.disabled = 0
        ORDER BY i.item_group, i.name
    """, as_dict=True)

    print(f"Found {len(rows)} supermarket items")

    # Clear old barcodes created by this script (rerun-safe)
    frappe.db.delete("Item Barcode", {
        "parent": ["in", [r.name for r in rows]]
    })

    seq_by_mfr = {}
    created = 0

    for item in rows:
        mfr = CATEGORY_MANUFACTURERS.get(item.item_group, "6289999")
        seq_by_mfr[mfr] = seq_by_mfr.get(mfr, 0) + 1
        barcode = make_ean13(mfr, seq_by_mfr[mfr])

        frappe.db.insert({
            "doctype": "Item Barcode",
            "name": frappe.generate_hash(length=10),
            "parent": item.name,
            "parenttype": "Item",
            "parentfield": "barcodes",
            "barcode": barcode,
            "barcode_type": "EAN",
            "idx": seq_by_mfr[mfr],
            "creation": frappe.utils.now(),
            "modified": frappe.utils.now(),
            "owner": "Administrator",
            "modified_by": "Administrator",
        })
        print(f"  {item.item_name[:45]:<45} → {barcode}")
        created += 1

    frappe.db.commit()
    print(f"\n✅ Done — {created} EAN-13 barcodes added.")
