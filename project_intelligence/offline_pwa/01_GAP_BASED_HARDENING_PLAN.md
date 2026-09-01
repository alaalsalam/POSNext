# Phase 7A Gap-Based Hardening Plan

## A. Already Good — Keep Unchanged

- Dexie-based `pos_next_offline` database and stores.
- Existing offline worker and worker client.
- Existing offline invoice queue/outbox.
- Server-side `Offline Invoice Sync` idempotency.
- Automatic sync on offline-to-online transition.
- POS header online/offline badge and pending invoice count.

## B. Exists but Needs Small Fix

### 1. PWA manifest scope mismatch

- Current implementation: generated manifest has `start_url: /pos` but `scope: /assets/pos_next/pos/`.
- Risk: browser install/routing may treat `/pos` as outside the PWA scope.
- Minimal fix: set generated manifest `scope` to `/pos` and add `id`, `lang`, and `dir`. Align the legacy `POS/manifest.webmanifest`.
- Files: `POS/vite.config.js`, `POS/manifest.webmanifest`.
- Migration: no.
- Test: build and inspect generated manifest.

### 2. Active cart recovery

- Current implementation: manual drafts exist, but the active unsaved cart is not automatically saved.
- Risk: refresh/browser crash can lose a cashier cart before payment.
- Minimal fix: persist a small localStorage recovery snapshot from the existing cart store and restore it when the same POS profile loads.
- Files: `POS/src/stores/posCart.js`.
- Migration: no.
- Test: static grep for recovery key and manual browser refresh test steps.

### 3. Failed sync visibility

- Current implementation: retry count exists; error is only easy to infer after max retries.
- Risk: cashier sees pending/failed invoices without a useful cause.
- Minimal fix: store `last_error` and `last_retry_at` on every failed sync attempt and display the latest error in the offline invoice dialog.
- Files: `POS/src/utils/offline/sync.js`, `POS/src/components/sale/OfflineInvoicesDialog.vue`.
- Migration: no. Dexie rows can store extra properties without schema/index changes.
- Test: static grep and manual sync failure test steps.

### 4. Stale cache warning

- Current implementation: cache last sync time is shown, but no clear stale warning.
- Risk: cashier may sell with old stock/pricing after days offline.
- Minimal fix: highlight stale cache age in the existing cache tooltip for 1/3/7 day thresholds.
- Files: `POS/src/components/pos/POSHeader.vue`.
- Migration: no.
- Test: static grep and manual old `lastSync` simulation.

## C. Missing and Critical

- Active cart recovery is critical for the business goal "cart survives refresh/browser crash".

## D. Missing but Optional

- Dedicated service-worker update prompt.
- Full browser automation offline-mode test suite.
- Rich install education/onboarding.

## E. Risky / Separate Phase

- Moving or widening service-worker scope to control `/pos` directly may require server headers or a root-scoped service-worker route. This should be handled as a deployment/app routing phase, not a quick Phase 7A patch.
- Changing backend schema for additional sync metadata is unnecessary in this phase.
