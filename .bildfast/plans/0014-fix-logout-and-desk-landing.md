<!-- bildfast:plan id=0014 status=approved agent=bildfast task="Fix the two pending items: logout button does nothing, and /desk doesn't land on POS" -->
# Plan: Fix logout button + make /desk land on the POS workspace

## Overview
User asked to fix the two pending items: (1) the logout button does nothing, and (2) opening
`/desk` doesn't show POS. Both were investigated evidence-first in a live browser, not guessed.

## 1. Logout button did nothing — REAL BUG, fixed
Reproduced live (logged in as the Phones cashier, opened the user menu → Sign Out → confirm):
the confirmation dialog opened, but clicking "خروج" did nothing and the page never left `/pos`.
The browser console showed `TypeError: Assignment to constant variable` fired from the Sign Out
click handler.

**Root cause:** in `POSSale.vue`, `_initializedKey` and `_posInitPromise` (the POS re-init
guard) were declared `const` but reassigned in several places — the init path, the
close-shift-then-logout path, and `confirmLogout()`. Every write threw; the one in
`confirmLogout()` aborted the function *before* `session.logout.submit()` ran, so Sign Out was a
no-op. The same throw also silently defeated the init guard (its key could never persist → POS
re-initialized redundantly on every remount).

**Fix:** changed both to `let`. Rebuilt, re-tested live: Sign Out now cleanly logs out and lands
on the login screen. Commit `ab1bcf3`.

## 2. /desk doesn't land on POS — Frappe-core landing behavior, bridged
Investigated in the browser + Frappe core router (`router.js`). Findings:
- Frappe v16 renders a curated **app-launcher grid** at the bare `/desk` route (only "hub"
  workspaces that have children — Accounting, Reports, etc.). POS is a standalone workspace with
  no children, so it never appears on that grid, and there's no persistent left sidebar there
  (the sidebar only shows on actual workspace pages, and even then collapses at narrow widths —
  a separate Frappe-core responsive behavior, confirmed identical at 780px and 1440px).
- Frappe's documented resolution order for the "home" workspace is (1) `User.default_workspace`,
  (2) private home, (3) the "home" workspace, (4)/(5) first workspace. But on a *hard load* of
  the empty route it shows the grid and does NOT honor `default_workspace`.

**Two-part fix:**
- **Data (this site):** set `User.default_workspace = "POS"` for all 15 POS cashier users +
  Administrator (so the preview session, which runs as Administrator, is covered). Cleared the
  per-user boot cache so it takes effect. Verified in `frappe.boot.user.default_workspace`.
- **Code (shippable):** reworked the previously-dead `public/js/desk_route_redirect.js` (it was
  never loaded, only handled legacy workspace names, and assumed `/app` while this site uses
  `/desk`) to also forward the **empty** Desk route to the user's own `default_workspace` — but
  ONLY when they have one set, so non-POS admins keep the stock grid. Enabled via
  `app_include_js` (Desk pages only — never the `/pos` SPA, web pages, or web forms).
  Loop-safe: only acts on the empty/legacy route, targets an existing workspace.

**Verified end-to-end** in the browser (as the Phones cashier, default_workspace=POS): running
the script takes `/desk` → `/desk/pos` and renders the full POS workspace (all sections + right
sidebar). Commit `abf31c6`.

**Caveat honestly stated:** `app_include_js` is read at gunicorn worker startup, and this host
runs `--preload` workers that I must not restart (shared multi-tenant bench — pos., lovable.,
etc.). The hook is already registered (confirmed via `frappe.get_hooks`) and the workers recycle
every 2000 requests (`--max-requests`), so the tag starts being served automatically as workers
roll — no restart from me required. Until a given worker recycles, its `/desk` still shows the
grid; `/desk/pos` and the sidebar work regardless.

## Not done / notes
- Did NOT touch the global "Strict User Permissions" system setting or any Frappe/ERPNext core
  file — stayed within `apps/pos_next/` + site data, per the operating rules.
- The `default_workspace` per-user values are site data (like the role/warehouse fixes earlier
  this session), not shipped in app code; the reusable mechanism (the redirect JS) is what ships.

## Follow-up — "Icon is not correctly configured" error on the Desk grid
User hit a Frappe popup ("Icon is not correctly configured please check the workspace sidebar")
when a POS workspace card was clicked on the `/desk` grid. Root cause: the canonical re-export
from `reinstall_workspace` (fix 0003) had written `link_type: "DocType"` onto the top-level POS
workspace (with `link_to` null) — Frappe's desktop grid then resolves that card to no route and
throws the error on click. Working workspaces (Accounting, Reports) have `link_type: null`.
Separately, `icon: "point-of-sale"` is not a real Frappe icon (rendered as a blank "P" avatar).
Fixed both — `link_type` → null, `icon` → `retail` (valid glyph) — in the live DB (DB data, so
consistent across all workers at once) and in `pos.json` (won't regress on reinstall). Verified
live: POS boots with the right values, renders cleanly, desk redirect lands on it with no error.
Commit `06bf996`.
