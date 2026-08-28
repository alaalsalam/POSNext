<!-- bildfast:plan id=0001 status=approved agent=bildfast task="Wire up unused 'Use Search Limit' POS Setting" -->
# Plan: Wire up the "Use Search Limit" POS Setting

## Overview
While explaining the "Advanced Settings > Use Search Limit / Search Result Limit" fields to
the user, discovered these fields (`use_limit_search`, `search_limit` on POS Settings) were
saved and validated but never actually read by the item search code — toggling them had zero
effect on real search behavior. The item search always used a fixed, device-performance-based
batch size (`performanceConfig.get("searchBatchSize")`) instead. User asked to fix the bug.

## Plan
- @bildfast (small, single-file fix, done inline — no sub-agent needed)
- `POS/src/stores/itemSearch.js` — in `searchItems()`, compute the effective search limit from
  `posSettingsStore.useLimitSearch` / `posSettingsStore.searchLimit` when the toggle is on,
  falling back to the existing device-based `performanceConfig` batch size when it's off.

## Execution Note
Changed `POS/src/stores/itemSearch.js` (~line 1670): the `searchLimit` used for both the
IndexedDB cache search and the server `get_items` call now reads
`posSettingsStore.useLimitSearch` / `posSettingsStore.searchLimit` (POS Settings > Advanced) when
enabled, instead of always using the device-performance auto-tuned batch size. When the toggle is
off, behavior is unchanged (device-based default). Rebuilt with `bench build --app pos_next`.
