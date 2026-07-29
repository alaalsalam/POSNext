# Digit POS Source of Truth and Deployment

This document defines the canonical source, naming, feature baseline, and deployment
workflow for Digit POS. Follow it to prevent development and production checkouts
from being mixed again.

## Canonical Application

Digit POS is **one Frappe application** deployed from two Git working copies because
development and production run in separate benches.

| Purpose | Bench | Repository checkout | Branch |
|---|---|---|---|
| Development and Lovable/BildFast | `frappe-bench16` | `/home/erpnext/frappe-bench16/apps/posnext` | `digitpos` |
| Production deployment | `frappe-bench-startd-prod` | `/home/erpnext/frappe-bench-startd-prod/apps/posnext` | `digitpos` |

The development checkout is the only source of new changes. The production checkout
must receive changes through Git fast-forward synchronization; never edit application
source directly in production.

## `posnext` and `pos_next` Are the Same App

- `posnext` is the Git repository directory name.
- `pos_next` is the Python package and Frappe app name.
- `apps/posnext` is the only application checkout directory in each bench.
- The former `apps/pos_next` alias symlinks were removed from both benches on
  2026-07-29 to prevent operators from mistaking them for duplicate repositories.
- `sites/assets/pos_next` is the Frappe static-assets symlink to
  `apps/posnext/pos_next/public`.

Therefore, references to `pos_next` in `sites/apps.txt`, Python imports, API routes,
and asset URLs refer to the app/package name—not to another checkout. The only
obsolete copy is the preserved archive:

`/home/erpnext/frappe-bench-startd-prod/archives/posnext-20260729`

Do not build, migrate, or copy source from that archive.

On these servers, replace generic documentation paths such as `apps/pos_next/POS`
with the real checkout path `apps/posnext/POS`.

## Feature Baseline

The `digitpos` branch includes the complete recent application work:

- POS sales, payments, returns, drafts, shifts, offline synchronization, and printing.
- Offers, coupons, referrals, branding, permissions, and Arabic localization.
- Catalog management, quick item creation, item groups, and selling/buying prices.
- Purchase Invoice creation, editing, submission, cancellation, and list/detail views.
- Supplier creation and selection.
- Supplier payments through ERPNext Payment Entry, including submit/cancel actions.
- Supplier payment history and outstanding purchase summaries.
- POS reporting for daily summaries, payment methods, recent transactions, and shifts.
- Backend tests for supplier payments and reporting.

Important implementation paths:

- `POS/src/components/purchases/`
- `POS/src/components/reports/`
- `POS/src/components/pos/CatalogManagement.vue`
- `pos_next/api/purchases.py`
- `pos_next/api/reports.py`
- `pos_next/api/catalog.py`
- `pos_next/api/permissions.py`
- `pos_next/tests/test_supplier_payments.py`
- `pos_next/tests/test_reports_api.py`

Recovery baseline:

- `9573cef` — purchasing, supplier payments, reporting, catalog, and recent UI work.
- `1f84966` — align `pypdf==6.10.2` with Frappe 16.22.0.

## Development Workflow

Lovable/BildFast must work only in:

```bash
cd /home/erpnext/frappe-bench16/apps/posnext
git switch digitpos
```

Before committing:

```bash
git status
git diff --check
cd POS
NODE_OPTIONS=--experimental-global-webcrypto yarn build
```

Commit from the development checkout:

```bash
cd /home/erpnext/frappe-bench16/apps/posnext
git add <intentional-files>
git commit -m "<clear change description>"
git push -u github digitpos
```

Do not commit generated platform-analysis directories such as `.bildfast/`, `.claude/`,
or `graphify-out/` as application source.

## Production Deployment

Synchronize production from the development checkout with a fast-forward merge:

```bash
cd /home/erpnext/frappe-bench-startd-prod/apps/posnext
git fetch origin digitpos
git merge --ff-only origin/digitpos
```

Build with readable production permissions:

```bash
cd /home/erpnext/frappe-bench-startd-prod/apps/posnext/POS
umask 022
NODE_OPTIONS=--experimental-global-webcrypto yarn build
find ../pos_next/public/pos -type d -exec chmod 755 {} +
find ../pos_next/public/pos -type f -exec chmod 644 {} +
```

Migrate, clear caches, and restart:

```bash
cd /home/erpnext/frappe-bench-startd-prod
bench --site pos.digit-erp.com migrate
bench --site pos.digit-erp.com clear-cache
bench --site pos.digit-erp.com clear-website-cache
bench restart
```

## Mandatory Verification

Both checkouts must resolve to the same commit:

```bash
git -C /home/erpnext/frappe-bench16/apps/posnext rev-parse HEAD
git -C /home/erpnext/frappe-bench-startd-prod/apps/posnext rev-parse HEAD
```

Production must import every editable application from the production bench:

```bash
/home/erpnext/frappe-bench-startd-prod/env/bin/python -m pip list --editable
```

No production environment link may point to `frappe-bench16`:

```bash
rg '/home/erpnext/frappe-bench16' \
  /home/erpnext/frappe-bench-startd-prod/env/lib/python3.14/site-packages \
  --glob '*.pth' --glob 'direct_url.json'
```

The expected output of the last command is empty.

Verify the runtime:

```bash
curl -I https://pos.digit-erp.com/pos/account/login
supervisorctl status | rg frappe-bench-startd-prod
```

The page and referenced assets must return HTTP `200`, and all production services
must report `RUNNING`.

## Recovery and Safety

- Never use `git reset --hard` to deploy.
- Never copy individual source files between benches.
- Preserve unexpected production changes in a named Git stash before synchronization.
- Use `git merge --ff-only` so production cannot silently create a divergent history.
- Keep the archived directory only as a historical backup; it is not a deployment source.
- Generated frontend assets may have different hash names per build; the served HTML
  and files must come from the same production build.
