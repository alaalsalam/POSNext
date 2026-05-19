# Phase 7A Limitations And Next Phase

## Remaining Limitations

- The Service Worker is generated under `/assets/pos_next/pos/sw.js`. The manifest scope is now aligned with `/pos`, but true browser control of `/pos` depends on service-worker registration scope and server headers. If the browser refuses a wider scope, a separate routing/header phase is needed.
- `sw.js` is served from the assets path and currently receives long cache headers. That can slow service-worker update rollout. This should be solved with deployment header rules or a root-scoped service-worker route.
- The active cart recovery snapshot is local to the current browser/device. It is not meant to sync carts across devices.
- Stale data warnings are informational; they do not block sales.
- Full offline regression testing with Playwright/Chrome offline emulation was not added in this phase.

## Recommended Next Phase

1. Browser-scope verification:
   - Use Chrome DevTools Application panel.
   - Confirm which pages are controlled by the Service Worker.
   - Confirm installability criteria.

2. Deployment header fix:
   - Avoid year-long caching on the service-worker script.
   - If needed, allow service worker scope to cover `/pos`.

3. Browser automation:
   - Add Playwright tests for:
     - first online load,
     - installability metadata,
     - offline refresh,
     - cart recovery,
     - offline invoice queue,
     - reconnection sync,
     - duplicate submit prevention.

4. Optional UX:
   - Add a visible "new version available" prompt instead of logging only.
   - Add a stronger long-offline banner when cache age exceeds 3 or 7 days.
