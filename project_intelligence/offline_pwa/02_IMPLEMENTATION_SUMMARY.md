# Phase 7A Implementation Summary

## Scope

This phase strengthened the existing offline/PWA implementation. It did not rebuild offline support, did not add a second IndexedDB layer, did not add a second outbox, and did not add a second Service Worker.

## Changes Implemented

### PWA Manifest Hardening

- Updated the generated PWA manifest configuration in `POS/vite.config.js`.
- Set:
  - `id: /pos`
  - `start_url: /pos`
  - `scope: /pos`
  - `lang: ar`
  - `dir: rtl`
  - `categories: business, productivity`
- Aligned the legacy/static `POS/manifest.webmanifest` so it no longer contradicts the generated manifest.

### Active Cart Recovery

- Added a small localStorage recovery snapshot in `POS/src/stores/posCart.js`.
- The snapshot is keyed by POS Profile.
- It stores only the active unsaved cart state.
- It expires after 24 hours.
- It is cleared when the cart is cleared or an invoice submits successfully.
- It restores only when the same POS Profile loads and the current cart is empty.

### Sync Failure Visibility

- Updated `POS/src/utils/offline/sync.js` to store `last_error` and `last_retry_at` on every failed sync attempt.
- Updated `POS/src/components/sale/OfflineInvoicesDialog.vue` to show the last sync error in both the list and detail view.

### Stale Cache Warning

- Updated `POS/src/components/pos/POSHeader.vue`.
- The cache tooltip now warns if cached item/stock/price data is older than:
  - 1 day,
  - 3 days,
  - 7 days.

## Migration

No schema changes were introduced.

`bench migrate` was not run.

## Files Changed for Phase 7A

- `POS/vite.config.js`
- `POS/manifest.webmanifest`
- `POS/src/stores/posCart.js`
- `POS/src/utils/offline/sync.js`
- `POS/src/components/sale/OfflineInvoicesDialog.vue`
- `POS/src/components/pos/POSHeader.vue`
- `project_intelligence/offline_pwa/*.md`

## Items Deliberately Not Changed

- Existing Dexie schema.
- Existing offline worker.
- Existing offline invoice queue.
- Existing backend `Offline Invoice Sync` DocType.
- Existing POS invoice submit flow.
- Service worker location/scope routing beyond manifest hardening, because widening the actual browser service-worker scope may require server headers or a root-scoped route and should be a separate deployment phase.
