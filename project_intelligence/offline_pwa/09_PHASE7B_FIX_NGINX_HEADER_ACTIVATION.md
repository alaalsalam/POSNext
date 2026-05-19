# Phase 7B-FIX - Nginx Header Activation

## Summary

The POSNext Service Worker scope fix was added to the bench Nginx config for
`pos.yemenfrappe.com`, but it is not active yet because the `frappe` user cannot run
`sudo -n nginx -t` or reload Nginx without a password.

## Nginx Config Path

```text
/home/frappe/frappe-bench/config/nginx.conf
```

This file is symlinked from:

```text
/etc/nginx/conf.d/frappe-bench.conf
```

## Added Location Block

The following exact-location block was inserted inside the HTTPS server block for
`pos.yemenfrappe.com`, before the generic `/assets` location:

```nginx
location = /assets/pos_next/pos/sw.js {
    root /home/frappe/frappe-bench/sites;
    try_files $uri =404;

    add_header Service-Worker-Allowed "/pos/" always;
    add_header Cache-Control "no-cache, no-store, must-revalidate" always;
    add_header Pragma "no-cache" always;
    add_header Expires "0" always;
}
```

## Activation Status

- Config file modified: yes.
- `sudo -n nginx -t`: failed because sudo requires a password.
- Nginx reload: failed because sudo requires a password.
- Runtime headers after attempted reload: unchanged.

## Required Manual Activation

Run as a sudo-capable user:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

After reload, run:

```bash
curl -sI https://pos.yemenfrappe.com/assets/pos_next/pos/sw.js | egrep -i 'HTTP|content-type|cache-control|service-worker-allowed|pragma|expires'
cd /home/frappe/frappe-bench/apps/pos_next
NODE_PATH=/home/frappe/frappe-bench/apps/pos_next/POS/node_modules node project_intelligence/offline_pwa/tools/verify_pos_pwa_control.js
```

Expected success:

- `Service-Worker-Allowed: /pos/`
- `Cache-Control: no-cache, no-store, must-revalidate`
- browser verification reports `controlled_by_sw: true` after clean unregister/cache clear/reload.
