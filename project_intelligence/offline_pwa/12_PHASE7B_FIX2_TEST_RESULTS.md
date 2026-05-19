# Phase 7B-FIX2 - Test Results

## Build

- `npm run build`: passed.
- `bench build --app pos_next`: passed.
- Existing unrelated `apps/doppio/node_modules` symlink warning still appears during bench build.

## Generated HTML

After setting `injectRegister: false`, generated POS HTML no longer includes:

```text
registerSW.js
vite-plugin-pwa:register-sw
virtual_pwa-register
```

The app now relies on the explicit registration in `POS/src/main.js`.

## Runtime Headers

Current runtime headers still show:

```text
Service-Worker-Allowed: /pos/
Cache-Control: no-cache, no-store, must-revalidate
```

The config file has been changed to `/pos`, but runtime has not loaded the change because
`sudo -n nginx -t` and reload are unavailable to the `frappe` user.

## Browser Verification

Browser verification was run after unregistering SW registrations and clearing caches.

Current result:

- `controlled_by_sw`: false
- registrations: 0
- blocker: scope `/pos` is rejected while runtime header remains `/pos/`

Expected result after sudo Nginx reload:

- `Service-Worker-Allowed: /pos`
- registration scope: `https://pos.yemenfrappe.com/pos`
- active script URL: `https://pos.yemenfrappe.com/assets/pos_next/pos/sw.js`
- `controlled_by_sw`: true

## Required Manual Step

Run as a sudo-capable user:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Then rerun:

```bash
cd /home/frappe/frappe-bench/apps/pos_next
NODE_PATH=/home/frappe/frappe-bench/apps/pos_next/node_modules node project_intelligence/offline_pwa/tools/verify_phase7b_fix2_sw_registration_scope.js
```
