<!-- bildfast:plan id=0004 status=approved agent=bildfast task="Sync leftover offline invoices on startup, not just on live reconnect" -->
# Plan: Sync leftover offline invoices on startup

## Overview
User reported: invoices get recorded offline and never get transferred to the server even
though the system is online. Traced this in code (`offlineState.js`, `stores/posSync.js`,
`utils/offline/sync.js`, `composables/useOffline.js`, `workers/offline.worker.js`) — the
**only** automatic sync trigger anywhere in the app is a reactive listener that fires when it
observes an offline→online *transition* while the page is open (`wasOffline && !nowOffline`
in `posSync.js`).

That means: an invoice queued offline, followed by a page reload / reopening the POS while
already online (no transition observed during that fresh session), never gets picked up
automatically — it just sits in the local IndexedDB queue until the cashier notices it in the
"offline invoices" dialog and syncs manually, or a live offline→online blip happens to occur
during that session.

## Plan
- @bildfast (single-file, frontend-only, low risk — reuses the existing, already-used
  `syncPending()`/`syncOfflineInvoices()` sync path; done inline, no sub-agent)
- `POS/src/stores/posSync.js`: on store creation, after loading the pending-invoice count, if
  the app is online and there's a backlog, call the existing `syncPending()` immediately
  instead of waiting for a live transition.

## Execution Note
Changed `POS/src/stores/posSync.js` (INITIALIZATION section, ~line 448): the store now awaits
`updatePendingCount()` right after creation and, if `!offlineState.isOffline` and there are
pending invoices/payments, calls the existing `syncPending()` — same function already used by
the reconnect listener and the manual "Sync"/"Retry" buttons, so no new sync logic was
introduced, just an additional trigger point. Wrapped in try/catch (failure is logged, not
thrown) so a sync hiccup can never block POS startup.

Verified:
- `npx biome lint` clean on the changed file.
- `bench build --app pos_next` succeeded; confirmed the new code path is present in the
  built `POSSale-*.js` bundle.
- Reasoned through the guard conditions: no pending invoices → no-op; offline at startup →
  no-op (falls back to the existing reconnect-triggered sync); sync failure → caught and
  logged, doesn't block the rest of POS init. No permission surface changes (reuses
  `submit_invoice`'s existing server-side checks).
- Did not run a full live-browser simulation (queue an invoice offline, reload while online,
  confirm the network call) on the shared demo site, to avoid creating stray test invoices
  against live demo company data — flagged to the user as available on request.

Committed separately as `fix: sync leftover offline invoices on startup, not just on live
reconnect` (commit 0750139), per the user's one-fix-per-commit policy. Two other
already-finished fixes from earlier in this session (search-limit wiring, payment/print
speed) were also committed separately at the same time (704391e, 178101e) to align with that
policy.
