# Phase 7B-FIX - Test Results

## Pre-Fix Baseline

- `sw.js` URL: `https://pos.yemenfrappe.com/assets/pos_next/pos/sw.js`
- `Service-Worker-Allowed`: missing
- `Cache-Control`: `max-age=31536000`
- Browser scope: `https://pos.yemenfrappe.com/assets/pos_next/pos/`
- `/pos` controlled by Service Worker: no

## Nginx Edit

Config path:

```text
/home/frappe/frappe-bench/config/nginx.conf
```

Inserted exact location under the `pos.yemenfrappe.com` HTTPS server block at approximately
line 4543.

## Config Test / Reload

- `sudo -n nginx -t`: failed, `sudo: a password is required`
- `sudo -n systemctl reload nginx`: failed, `sudo: a password is required`

Because reload did not run, the active runtime Nginx process still serves old headers.

## Post-Edit Curl Result

`curl -sI https://pos.yemenfrappe.com/assets/pos_next/pos/sw.js` still returns:

```text
HTTP/2 200
content-type: application/javascript
cache-control: max-age=31536000
```

`Service-Worker-Allowed` is still absent at runtime.

## Browser Verification

Re-running browser verification still reports:

- `navigator.serviceWorker`: available
- registration count: 1
- active script: `https://pos.yemenfrappe.com/assets/pos_next/pos/sw.js`
- active scope: `https://pos.yemenfrappe.com/assets/pos_next/pos/`
- target `/pos/` scope: false
- `/pos` controlled by SW: false

## Conclusion

The Nginx config file now contains the required exact-location rule, but activation is pending
root-level `nginx -t` and reload.
