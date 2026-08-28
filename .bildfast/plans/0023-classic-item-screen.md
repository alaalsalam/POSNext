<!-- bildfast:plan id=0023 status=approved agent=claude task="Classic item management screen" -->
# Plan: Classic item management screen (شاشة الأصناف الكلاسيكية)

## Overview
Rebuild **إدارة الأصناف** into a classic desktop-style master–detail item screen matching the
attached reference: a fixed top **toolbar** (إضافة / حفظ / تعديل / حذف / بحث + record-navigation
◄◄ ◄ ► ►►), a peach RTL **form** with all requested fields, and a **data grid** below ordered by
the auto item code. One screen for three jobs: add a new item, update its stock/prices, and query a
specific item.

Most of the plumbing already exists and will be **reused, not rebuilt**:
- `pos_next/api/items.py` — `get_items` / `get_item_details` / `get_item_stock` (listing + stock).
- `pos_next/api/catalog.py` — item + item-group creation, selling/buying `Item Price`.
- `pos_next/api/inventory.py` — `submit_pos_stock_reconciliation` (already the app's stock-setting
  mechanism, with `custom_pos_buying_rate` / `custom_pos_selling_rate`) + a dedicated Inventory
  Adjustment screen.

## Field mapping (defaults decided; two need YOUR choice — see Questions)
| Field (AR) | Maps to | Notes |
|---|---|---|
| اسم الصنف | `Item.item_name` | existing |
| كود الصنف (تسلسلي تلقائي) | `Item.item_code` via a POS naming series (`POS-ITEM-.####`) | applied ONLY on create from this screen; does NOT change Item's global autoname |
| اسم المجموعة | `Item.item_group` | existing picker + create-group |
| وحدة الصنف | `Item.stock_uom` | existing |
| الوصف | `Item.description` | existing |
| الباركود | `Item Barcode` | existing `_assert_barcode_unique` |
| صورة الصنف | `Item.image` | Frappe standard upload |
| السريال | **NEW** custom Data field `custom_pos_serial` on Item | a model/reference string (as in the screenshot), NOT ERPNext per-unit Serial No — enabling `has_serial_no` would force serial entry on every sale and break the POS flow |
| سعر التكلفة | buying `Item Price` | existing |
| سعر البيع | selling `Item Price` | existing |
| ~~سعر التجزئة~~ | — | **REMOVED per user** |
| الكمية | writes stock (see Decisions Q1=A) | Add = add purchased qty; Edit = set to new value |
| الكمية المتاحة | `Bin.actual_qty − Bin.reserved_qty` (display-only) | reserved already comes from Sales Orders; **no POS-level reservation system is built** — the "في حال أردنا حجز كمية" note is a separate future feature |

## Plan
**Backend — `@bildfast-backend` (me):** new unified endpoints in `catalog.py`, all manager-gated
(`canManageCatalog` / Item create+write), company-scoped, and N+1-safe (batch Bin/price lookups):
- `get_catalog_items(pos_profile, search, limit, offset)` → grid rows (code, name, group, uom, qty,
  available, cost, selling, retail, barcode, serial), **ordered by code**.
- `get_catalog_item(item_code, pos_profile)` → one item, all fields (for query/edit).
- `save_catalog_item(...)` → create **or** update: item fields + barcode + serial + image + the 3
  prices (+ stock per Q1). Extends `create_quick_item`; adds the update path.
- `delete_catalog_item(item_code, pos_profile)` → guards items that already have stock ledger /
  transactions (disable rather than hard-delete when unsafe).
- Ship `custom_pos_serial` (custom/item.json + patch); retail-price plumbing per Q2; reuse
  `submit_pos_stock_reconciliation` for stock (Q1-A) — no duplicate stock logic.
- Unit + integration tests for every endpoint (happy + error/permission paths).

**Frontend — `@bildfast-frontend`** (brief includes the reference screenshot):
- Replace `CatalogManagement.vue` with the classic screen — peach RTL form, bordered inputs, fixed
  toolbar, data grid ordered by code, image upload, item-group search. Record-navigation arrows are
  a **client-side cursor** over the sorted list (UI state, not an API). Keep the existing rail/mobile
  entry point.
- **Toolbar semantics (per user):**
  - **إضافة (Add):** clear the form for a NEW item; the الكمية field is the **purchased quantity to
    add to stock**. Save → create the item + set its stock to that qty + cost/selling prices.
  - **تعديل (Edit):** first **select a row in the grid**, then Edit loads it into the form; the admin
    changes any field (qty, prices, name, …) → Save updates the item (qty → reconciled to the new
    value). **Edit is admin/manager-only.**
  - **حذف (Delete):** remove the selected item (guarded). **بحث (Search):** filter/query. **Arrows:**
    move the record cursor over the sorted grid.
- Edit/Delete buttons are enabled only for admins (`canManageCatalog`) and only when a row is
  selected; Add is available on the screen as today.

**Replacement:** the classic screen **replaces** today's quick-add CatalogManagement.vue (same entry
point). Say if you'd rather keep the quick-add as a separate tab.

## Decisions (from user — locked)
- **Q1 = A** — الكمية **يكتب المخزون** via the existing reconciliation mechanism. **Add** adds the
  purchased quantity (new item, stock 0 → qty). **Edit** sets stock to the edited value (reconcile).
  Cost price feeds the valuation rate.
- **Q2 = remove** — **سعر التجزئة deleted**; only سعر التكلفة (cost) + سعر البيع (selling) remain.
- **Permissions** — the whole screen is admin/manager-gated as today; **Edit (modifying an existing
  item's qty/prices) is admin-only**. (If Add — receiving purchased stock — should also be open to
  regular cashiers, that's a one-line follow-up; default keeps it manager-gated.)

## Execution Note
**Backend — DONE & committed (`854f5f1`), verified end-to-end as a POS Manager.**
- New endpoints in `pos_next/api/catalog.py`: `get_catalog_items`, `get_catalog_item`,
  `create_catalog_item`, `update_catalog_item`, `delete_catalog_item` (all company-scoped,
  N+1-safe, feature-gated via `_context`).
- `custom_pos_serial` Data field added to Item via patch `v2_1_0/add_pos_item_serial_field.py`.
- Stock is written by reusing `inventory.submit_pos_stock_reconciliation` (cost → valuation);
  prices are the existing selling/buying `Item Price`. 14 mock-based unit tests
  (`tests/test_catalog_screen.py`), all green.
- **Auto code** = a clean `POS-ITM-#####` series (collision-free). A plain integer sequence was
  avoided because this app also uses long barcode numbers as item codes, which made a numeric
  `max+1` jump to huge/uneven values — the series stays predictable. (Easy to change if a plain
  sequence is preferred.)
- **Delete** = soft-disable by default (POS Managers hold Item *write* but not *delete*); a real
  hard-delete happens only when the caller has Item delete permission and the item has no stock
  history.
- **Create** uses `ignore_permissions=True` on the Item insert, justified: the endpoint already
  checks the catalog flag + Item `create` permission + company scope, and the company-isolation
  `validate` hook binds ownership — the framework's per-doc check otherwise defers new company-owned
  items to a check a warehouse-scoped manager fails, even for their own catalog.

**Frontend — delegated to `@bildfast-frontend`** (classic screen replacing `CatalogManagement.vue`),
built against the contract above with the reference screenshot. Pending its build + verification.

**Note:** `enable_catalog_management` must be ON for a profile to use this screen (as today).
`سعر التجزئة` intentionally omitted per the decisions above.
