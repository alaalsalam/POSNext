# Phase 7B - Test Results

## Commands

The following checks were used during Phase 7B:

- `curl -I https://pos.yemenfrappe.com/pos`
- `curl -I https://pos.yemenfrappe.com/assets/pos_next/pos/sw.js`
- `curl -I https://pos.yemenfrappe.com/assets/pos_next/pos/manifest.webmanifest`
- `curl -I https://pos.yemenfrappe.com/pos/sw.js`
- `python3 project_intelligence/offline_pwa/tools/verify_phase7b_offline_pwa.py`
- `node project_intelligence/offline_pwa/tools/verify_pos_pwa_control.js`
- `npm run build`
- `bench build --app pos_next`

## HTTP Results

- `/pos`: 200 OK.
- `/assets/pos_next/pos/manifest.webmanifest`: 200 OK and valid JSON.
- `/assets/pos_next/pos/sw.js`: 200 OK and JavaScript.
- `/pos/sw.js`: 200 OK but returns HTML, not a Service Worker script.

## Header Results

- `Service-Worker-Allowed` on `sw.js`: missing.
- `Cache-Control` on `sw.js`: `max-age=31536000`.
- Result: current deployed headers are not ready for reliable `/pos/` Service Worker control.

## Offline Regression Results

- Dexie database exists.
- `invoice_queue` store exists.
- Local `offline_id` is unique.
- Server `Offline Invoice Sync.offline_id` is required and unique.
- No database schema change was introduced.

## Browser Results

Browser verification was performed by `tools/verify_pos_pwa_control.js` and writes:

- `sites/pos.yemenfrappe.com/private/files/posnext_phase7b_browser_control_result.json`

Observed browser result:

- `navigator.serviceWorker`: available.
- Registration count: 1.
- Active script: `https://pos.yemenfrappe.com/assets/pos_next/pos/sw.js`.
- Active registration scope: `https://pos.yemenfrappe.com/assets/pos_next/pos/`.
- `controlled_by_sw`: `false`.
- Target `/pos/` scope present: `false`.
- Cache names included Workbox precache and API cache.

This confirms the deployment issue: the SW is alive, but it is scoped to the assets directory
and does not control the POS route.

## Build Results

- `npm run build`: passed.
- `bench build --app pos_next`: passed.
- No `migrate` was run.
- No restart was run.
- Cache and website cache were cleared.
