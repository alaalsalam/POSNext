# Phase 7B-FIX2 - Explicit Service Worker Registration Scope

## Summary

This phase changed the POSNext PWA registration from the generated VitePWA default scope to
an explicit POS route scope.

## Previous Failure

The Service Worker script is served from:

```text
/assets/pos_next/pos/sw.js
```

VitePWA's generated registration was using the default scope:

```text
/assets/pos_next/pos/
```

After Nginx was configured with `Service-Worker-Allowed: /pos/`, the browser correctly
rejected that default asset scope.

## Canonical POS URL

Runtime curl showed:

- `/pos`: HTTP 200
- `/pos/`: HTTP 301 to `/pos`

Therefore the canonical POS URL is `/pos`, not `/pos/`.

## Scope Decision

The selected registration scope is:

```text
/pos
```

Reason: it covers the actual canonical page `/pos`. A `/pos/` scope would not control the
initial `/pos` document.

## Source Changes

Changed:

- `POS/src/main.js`
- `POS/vite.config.js`

`POS/src/main.js` now registers the existing generated Service Worker explicitly:

```js
navigator.serviceWorker.register("/assets/pos_next/pos/sw.js", {
  scope: "/pos",
  updateViaCache: "none",
})
```

`POS/vite.config.js` sets:

```js
injectRegister: false
```

This prevents VitePWA from injecting `registerSW.js`, which was still attempting the old
asset-directory scope.

## Manifest

The manifest remains aligned with `/pos`:

- `id`: `/pos`
- `start_url`: `/pos`
- `scope`: `/pos`

## Nginx

The bench Nginx config was changed from:

```text
Service-Worker-Allowed: /pos/
```

to:

```text
Service-Worker-Allowed: /pos
```

Runtime still shows `/pos/` until Nginx is reloaded with sudo.

## Migration / Restart

- No migrate was run.
- No application restart was run.
- Nginx reload is still required to activate the header path change.
