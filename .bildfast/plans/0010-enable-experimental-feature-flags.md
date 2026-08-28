<!-- bildfast:plan id=0010 status=approved agent=bildfast task="Enable the 4 experimental POS Settings feature flags across all companies for continued development" -->
# Plan: Enable catalog management / purchases / supplier payments / POS reports everywhere

## Overview
Following up on the previous "what's hidden/disabled" question — user asked to turn on the 4
experimental feature flags (`enable_catalog_management`, `enable_purchases`,
`enable_supplier_payments`, `enable_pos_reports`) so development/testing can continue on top of
them, instead of leaving them off by default.

This is a **data/configuration change**, not a code change — the flags and their toggle UI
already exist (built and shipped); nothing new was written. No `business.md`/`tests.md` update
needed (no capability was added/removed — these features already existed, just switched from
off to on), and no plan-then-approve gate applies (this isn't new backend/frontend work).

## Plan
- @bildfast — update all 15 `POS Settings` records (one per company/POS Profile) via
  `doc.update({...}); doc.save()` (not raw SQL) so `validate()` — including
  `validate_feature_dependencies()` and the `assert_feature_manager()` permission guard — and
  `on_update()` (syncs `allow_negative_stock` to Stock Settings, publishes the realtime
  feature-flag-changed event other open sessions listen for) run exactly as they would from the
  Desk UI. Ran as Administrator so the feature-manager permission check passes.

## Execution Note
Enabled all 4 flags on all 15 POS Settings records (Phones, Toys, Super Market, Restaurant,
Pizza, Pharmacy, Perfumes, Ice Cream, Hairdressing, Gold and Jewelry, Glasses, Flowers,
Electrical Appliances, Chocolates, Cafe) — `enable_catalog_management=1`,
`enable_purchases=1`, `enable_supplier_payments=1`, `enable_pos_reports=1`. All 15 saved
without validation errors (the `enable_supplier_payments` → `enable_purchases` dependency was
satisfied since both were set in the same update). Verified afterward: zero POS Settings
records remain with `enable_catalog_management=0`.

Cashiers still can't use catalog management specifically — that also requires
`can_manage_workflows` (System Manager/Sales Manager/POS Manager role) and doctype permission
on Item, per `pos_next/api/permissions.py`; the feature flag being on just makes it *possible*
for eligible roles, not universal.
