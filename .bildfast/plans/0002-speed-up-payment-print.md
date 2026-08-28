<!-- bildfast:plan id=0002 status=approved agent=bildfast task="Remove delay between payment completion and the print/success message" -->
# Plan: Remove delay between payment completion and the print/success message

## Overview
User reported a noticeable delay between completing a payment and seeing the
print/success message on `/pos`. Traced it to `handlePaymentCompleted()` in
`POS/src/pages/POSSale.vue` (online checkout path):

1. It `await`-ed `stockStore.refresh(...)` — a real network call — *before*
   printing/showing the success message, even though stock refresh has no
   bearing on what the cashier sees next (a classic sequential/waterfall call
   the house rules flag).
2. It then called `handlePrintInvoice({ name: invoiceName })`, passing only
   the invoice name. Since the invoice `items` array wasn't included, the
   print helper fell through to `printInvoiceByName()`, which does **two more
   sequential network calls** (`get_invoice`, then the POS Profile's print
   settings) before finally opening the print window — even though the
   invoice submission response (`invoice.as_dict()`) already contains the
   full invoice incl. `items`.

Combined, the cashier was waiting on up to 3 sequential network round-trips
before seeing any feedback.

## Plan
- @bildfast (small, single-file fix, done inline — no sub-agent needed)
- `POS/src/pages/POSSale.vue` — `handlePaymentCompleted()`:
  - Make `stockStore.refresh(...)` fire-and-forget (same non-blocking pattern
    already used for `loadInvoiceHistoryData()` right below it).
  - Pass the already-fetched submitted invoice (`submittedInvoice`, with its
    `items` array) into `handlePrintInvoice()` instead of just `{ name }`, so
    the browser/silent print path uses the data already on hand instead of
    re-fetching it.

## Execution Note
Changed `POS/src/pages/POSSale.vue` (~lines 2444-2477):
- `stockStore.refresh(...)` is no longer awaited before printing/showing
  success — it now runs in the background with a `.catch()` (same pattern as
  the existing background invoice-history refresh).
- Normalized `submittedInvoice = result.message || result` once, and pass
  `submittedInvoice` (which has `.items`) to `handlePrintInvoice()` on the
  auto-print/silent-print path, so `printInvoice()` opens the print window
  directly instead of going through `printInvoiceByName()`'s extra
  `get_invoice` + POS Profile print-settings fetches.
- Offline checkout path was already unaffected (it already hands
  `handlePrintInvoice` a full item-bearing doc via `uiStore.lastOfflinePrintDoc`).
- No behavior change when `autoPrintEnabled`/`silentPrint` are off — the
  success dialog now simply appears without waiting on the background stock
  refresh.
- Rebuilt with `bench build --app pos_next`.
