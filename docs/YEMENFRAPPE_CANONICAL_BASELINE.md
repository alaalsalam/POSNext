# YemenFrappe POSNext Canonical Baseline

Date: 2026-08-03

## Source of truth

The permanent source of truth is `YemenFrappe/posnext`, branch `develop`. All future
work must start from this branch. The former deployed `maward-version` checkout is a
rollback source only and must not receive new development.

Integration base: `0e957e3` (`yemenfrappe/develop`).

Pre-integration deployed revision: `cbe9397`, preserved as the local backup branch
`backup/maward-version-before-yemenfrappe-integration-20260803`.

## Selectively restored behavior

- Explicit `/pos` service-worker scope with update checks and no HTTP cache reuse.
- Cached bootstrap and POS settings fallback for offline startup.
- Twenty-four-hour, POS-profile-scoped recovery of an unsent active cart.
- Offline returns using the existing durable invoice queue.
- Offline partial payments with stable client references, retry metadata, failed-state
  recovery, deletion, counts, filters, and a combined Offline Operations screen.
- Server-side Payment Entry reference validation so replaying the same offline payment
  is idempotent and a reference collision fails closed.
- Cached read-only POS Settings, promotions, item lookup, variants, and POS-warehouse
  stock while offline. Administrative writes remain blocked during an outage.

## Validation before deployment

- `git diff --check`: passed.
- Python compile for `pos_next/api/partial_payments.py`: passed.
- Vitest: 6 files, 13 tests passed.
- Vite production build: passed; 2,188 modules transformed and PWA artifacts generated.
- Built JavaScript contains service-worker registration at
  `/assets/pos_next/pos/sw.js` with scope `/pos`.

The build retains known non-fatal warnings for external Digit/Nexus assets and mixed
static/dynamic imports. These warnings existed in the integration base and do not
represent a failed build.

## Deployment and rollback contract

Before deployment, create a site backup including files. Deploy only the canonical
`develop` checkout, rebuild assets, migrate, clear caches, restart services, and verify
`/pos`, `sw.js`, and the `Service-Worker-Allowed: /pos` response header.

If verification fails, switch the checkout back to
`backup/maward-version-before-yemenfrappe-integration-20260803`, rebuild assets, migrate
if required, clear caches, and restart. Restore the database/files backup only if the
migration or application writes require data rollback.

## Deployment evidence

Deployment to `pos.yemenfrappe.com` completed on 2026-08-03.

- Full backup completed at prefix
  `sites/pos.yemenfrappe.com/private/backups/20260803_222203-pos_yemenfrappe_com`.
- `bench build --app pos_next`, site migration, cache clearing, and service restart
  completed successfully.
- Live `/pos`: HTTP 200 with no-store/no-cache policy.
- Live hashed JavaScript asset: HTTP 200 and contains the explicit `/pos` service-worker
  registration.
- Live `sw.js`: HTTP 200, `Service-Worker-Allowed: /pos`, and no-cache headers.
- The install manifest and application icons are served from POSNext itself rather than
  the optional external Digit app, so PWA installation does not depend on another app.
- Optional Digit/Nexus stylesheet, font, and demo-banner references were removed from the
  runtime entry; POSNext now uses its bundled Almarai and Inter fonts without 404 assets.
- The deployment environment uses umask `0077`; the frontend build script now sets
  umask `022` so future generated public assets remain readable by Nginx.
