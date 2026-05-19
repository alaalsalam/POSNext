# Phase 7B - Service Worker Scope and Headers Audit

## Summary

Phase 7B audited the deployed POSNext PWA behavior for `https://pos.yemenfrappe.com/pos`.
The existing offline/PWA implementation is real and should not be rebuilt. The remaining
deployment risk is specifically the Service Worker script location and HTTP headers.

## Current Service Worker Registration

- Source registration: `POS/src/main.js`
- Registration helper: `virtual:pwa-register`
- Current options: `immediate: true`
- No explicit `scope` or `updateViaCache` is passed in source.
- Generated Service Worker URL: `/assets/pos_next/pos/sw.js`

## Manifest

- Deployed URL: `/assets/pos_next/pos/manifest.webmanifest`
- Status: reachable
- Current values:
  - `id`: `/pos`
  - `start_url`: `/pos`
  - `scope`: `/pos`
  - `lang`: `ar`
  - `dir`: `rtl`
  - `display`: `standalone`

The manifest values are correct for installability intent. However, manifest `scope` does
not widen Service Worker scope by itself.

## HTTP Header Findings

Observed deployed headers:

- `/pos`: HTTP 200, `content-type: text/html; charset=utf-8`
- `/assets/pos_next/pos/sw.js`: HTTP 200, `content-type: application/javascript`
- `/assets/pos_next/pos/sw.js`: `cache-control: max-age=31536000`
- `/assets/pos_next/pos/sw.js`: no `Service-Worker-Allowed`
- `/assets/pos_next/pos/manifest.webmanifest`: HTTP 200, `content-type: application/octet-stream`
- `/assets/pos_next/pos/manifest.webmanifest`: `cache-control: max-age=31536000`
- `/pos/sw.js`: HTTP 200, but returns the POS HTML page, not JavaScript

## Scope Impact

Because the active script is served from `/assets/pos_next/pos/sw.js`, the browser's default
maximum Service Worker scope is expected to be under `/assets/pos_next/pos/`. Without a
`Service-Worker-Allowed: /pos/` header, attempting to control `/pos/` from that script URL is
not reliable and should be treated as not production-ready.

## Offline Existing Capability Check

Existing offline internals remain present:

- Dexie database: `pos_next_offline`
- IndexedDB store: `invoice_queue`
- Local unique key: `&offline_id`
- Server DocType: `Offline Invoice Sync`
- Server `offline_id`: required and unique
- Outbox/error fields from Phase 7A remain in source.

## Decision

The right Phase 7B fix is not to create a second Service Worker or duplicate the offline
system. The correct deployment hardening is to serve the current SW script with safe SW
headers, or expose the same script under `/pos/sw.js` as JavaScript. Since this site serves
assets directly from Nginx, app-level Python hooks cannot reliably change the `/assets`
response headers.
