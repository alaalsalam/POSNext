<!-- bildfast:plan id=0013 status=approved agent=bildfast task="Give every ManagementSlider action a narrow-viewport fallback (not just Settings)" -->
# Plan: Make the Settings button reachable at narrow viewport widths

## Overview
User sent a screenshot from the actual BildFast preview (Phones POS, shift open, "Administrator"
preview session) asking why something still doesn't show — after the last several turns fixed
every backend permission needed. Investigated the actual UI code path instead of re-checking
permissions again, since those were already re-verified `True` for every user.

**Root cause, confirmed by reading the component tree (not guessed):** the Settings trigger is
rendered in exactly one place — `ManagementSlider.vue`, a `hidden lg:flex` icon-only sidebar
(desktop-only, ≥1024px). `Catalog Management`, `Purchases`, and `Reports` all have a **second**
implementation in `POSSale.vue`'s "Mobile/Tablet Management Actions" row (`lg:hidden`, the
fallback for narrower viewports) — but **Settings was never added to that fallback row**. Below
the `lg:` breakpoint, Settings has zero reachable UI, regardless of permissions — matching the
exact same class of issue found earlier this session with Frappe's own Desk sidebar collapsing
at narrow widths, except this one is inside pos_next's own code and is a real, fixable bug.

## Plan
- @bildfast (single file, one new button matching an existing established pattern exactly —
  done inline, no sub-agent)
- `POS/src/pages/POSSale.vue`: add a "Settings" button to the mobile/tablet management-actions
  row, gated by the same `canManageFeatureFlags` flag `ManagementSlider` already uses, calling
  the same `handleManagementMenuClick('settings')` handler already wired to open the dialog.

## Execution Note
Added the button (gear icon, matching the desktop version's icon) to the `lg:hidden` action
row, and added `canManageFeatureFlags` to that row's outer `v-if` so the row itself appears
when Settings is the *only* thing a user is allowed to manage (previously it only checked
catalog/purchases/reports). No new state, no new permission logic — reuses what's already
correctly wired for the desktop sidebar. `npx biome lint` clean. `bench build --app pos_next`
succeeded.

This fixes it for every user at narrow viewport widths, not just the ones whose access I fixed
in the previous few turns — the icon-strip visibility bug was independent of and downstream of
those permission fixes.

## Update — user asked to fix this "definitively"
Took that as "don't just patch the one reported symptom" and did two more things before calling
it done:

1. **Checked `ManagementSlider.vue` for other gaps, not just Settings.** It has 7 actions total:
   Promotions, Products (Stock Lookup), Invoices, Purchases, Reports, Catalog, Settings. Only 3
   of the 7 (Catalog/Purchases/Reports) had ever been ported to the mobile fallback row —
   Promotions, Products, and Invoices were in the *exact same broken state* as Settings (no
   permission gate on the desktop side either — they're available to every user with an open
   shift, so this was a bigger blast radius than the manager-only features). Added all three so
   the mobile row now has 1:1 parity with the desktop sidebar, all 7 actions.
2. **Grepped the rest of the app for the same `hidden lg:flex` (desktop-only, no fallback)
   pattern**, rather than assuming this was the only spot: found it twice more, in
   `POSHeader.vue` (time/shift-duration display) and `PaymentDialog.vue` (payment action
   buttons incl. "Complete Payment" and "Pay on Account"). Read both — both already have a
   proper, separate mobile-equivalent button/element elsewhere in the same file (confirmed by
   reading the code, not assumed), so neither needed a change. `ManagementSlider` was the only
   genuine gap in the app.

Rebuilt and committed the Promotions/Products/Invoices addition separately
(`f097dc7`) from the original Settings-only fix (`89ace8d`), since they were found and reasoned
about in two distinct passes even though they land in the same file/block.
