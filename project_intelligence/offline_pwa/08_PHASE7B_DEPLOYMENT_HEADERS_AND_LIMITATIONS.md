# Phase 7B - Deployment Headers and Limitations

## Required Deployment Header Fix

The current generated Service Worker is:

```text
/assets/pos_next/pos/sw.js
```

To allow it to control `/pos/`, Nginx must return a widened scope header for this exact file
and must avoid long-lived caching for the Service Worker script.

## Minimal Nginx Snippet

Use a site-specific snippet before the generic `/assets` location if possible:

```nginx
location = /assets/pos_next/pos/sw.js {
    alias /home/frappe/frappe-bench/sites/assets/pos_next/pos/sw.js;
    default_type application/javascript;
    add_header Service-Worker-Allowed "/pos/" always;
    add_header Cache-Control "no-cache, no-store, must-revalidate" always;
    add_header Pragma "no-cache" always;
    add_header Expires "0" always;
}
```

Optional manifest content-type/cache polish:

```nginx
location = /assets/pos_next/pos/manifest.webmanifest {
    alias /home/frappe/frappe-bench/sites/assets/pos_next/pos/manifest.webmanifest;
    default_type application/manifest+json;
    add_header Cache-Control "no-cache" always;
}
```

## Activation Commands

Run only after placing the snippet in the active Nginx config:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

If this bench is managed by generated Frappe Nginx config, preserve the snippet in the
appropriate custom include so `bench setup nginx` does not erase it.

## Why This Was Not Applied Automatically

Phase 7B is committed inside `apps/pos_next`. The active Nginx config is server-level
deployment configuration, not app source. Applying it automatically would create a server
state change outside the app commit and could be overwritten by future bench config
generation.

## Current Limitation Until Header Activation

- Manifest is valid and app installability metadata is good.
- Offline IndexedDB/outbox code remains available.
- `/pos` Service Worker control is not considered verified for production until:
  - `Service-Worker-Allowed: /pos/` is present on `sw.js`, and
  - `sw.js` uses no-cache/no-store or max-age=0, and
  - browser verification reports `controlled_by_sw: true`.
