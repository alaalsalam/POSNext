# Phase 7A Test Results

## Commands Run

### POS Frontend Build

Command:

```bash
cd apps/pos_next/POS
npm run build
```

Result: passed with Node `v20.19.0`.

### Bench Build

Command:

```bash
bench build --app pos_next
```

Result: passed with Node `v20.19.0`.

Notes:

- The unrelated existing `apps/doppio/node_modules` symlink warning appeared during asset linking.
- Vite reported existing dynamic/static import chunk warnings for `bootstrap.js` and `currency.js`; build completed successfully.

### Cache Clear

Command:

```bash
bench --site pos.yemenfrappe.com clear-cache
bench --site pos.yemenfrappe.com clear-website-cache
```

Result: passed.

## PWA Checks

- `/assets/pos_next/pos/manifest.webmanifest` returns valid JSON.
- Manifest now includes:
  - `id: /pos`
  - `start_url: /pos`
  - `scope: /pos`
  - `display: standalone`
  - `lang: ar`
  - `dir: rtl`
  - icons for any and maskable purposes.
- `/pos/` redirects to `/pos` and returns HTTP 200.
- `/pos` HTML links `/assets/pos_next/pos/manifest.webmanifest`.

## Service Worker Checks

- `/assets/pos_next/pos/sw.js` exists.
- Generated service worker contains:
  - `precacheAndRoute`
  - `cleanupOutdatedCaches`
  - `skipWaiting`
  - `clientsClaim`
  - `pos-assets-cache`
  - `product-images-cache`
  - `api-cache`
  - `pos-page-cache`
- Offline worker bundle exists in the build output.

## IndexedDB / Outbox Checks

- Dexie schema remains unchanged.
- `invoice_queue` still has unique `offline_id`.
- Backend DocType `Offline Invoice Sync` has `offline_id` marked unique and required.
- No schema migration was needed.

## Static Code Checks

Verified built/source code contains:

- `pos_next_active_cart_recovery`
- `last_error`
- `last_retry_at`
- `Last sync error`
- stale-cache warnings.

## Manual Tests To Run In Browser

1. Open `/pos`, login, open a shift.
2. Add 2 items to cart.
3. Refresh the browser tab.
4. Confirm the cart is restored and a recovery warning appears.
5. Clear cart and refresh again.
6. Confirm the cleared cart does not return.
7. Turn off network after initial cache sync.
8. Create an offline invoice.
9. Confirm it appears in the offline invoice dialog and pending badge.
10. Reconnect network and use Sync All.
11. Confirm it syncs once and does not duplicate.

## Automated Browser Offline Test

Not run in this phase. The environment did not require installing browser dependencies, and Phase 7A focused on gap-based hardening plus build/static verification.
