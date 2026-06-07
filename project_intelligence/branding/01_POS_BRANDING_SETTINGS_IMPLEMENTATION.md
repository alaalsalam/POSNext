# POS Branding Settings Implementation

## What Was Hardcoded

- Fixed POS identity appeared in login, home, POS sale, POS header, PWA install UI, receipt fallback, error reports, static manifest, and Desk workspace metadata.
- The local receipt fallback had a fixed external footer line.
- The packaged workspace used a customer-specific name and route.

## What Was Moved To Settings

A Single DocType named `POS Branding Settings` now controls visible POS identity through `pos_next.api.branding.get_pos_branding_settings`.

Configured fields:

- `enabled`
- `app_name`
- `app_short_name`
- `workspace_label`
- `login_title`
- `login_subtitle`
- `primary_logo`
- `header_logo`
- `app_icon`
- `pwa_icon_192`
- `pwa_icon_512`
- `primary_color`
- `secondary_color`
- `theme_color`
- `background_color`
- `install_button_label`
- `receipt_title`
- `receipt_footer`
- `demo_banner_enabled`
- `demo_banner_text`
- `custom_css_optional`

Fallback values are generic:

- `app_name`: `POSNext`
- `app_short_name`: `POS`
- `workspace_label`: `POS`

No customer name is used as source-code fallback.

## Where Branding Appears

- Browser title and PWA theme meta tags.
- Login title, subtitle, and logo.
- POS header name, logo, version badge colors, and install label.
- Home and POS sale product text.
- Mobile install banner icon, title, and button label.
- Local receipt title/footer fallback.
- Error report heading.
- Optional demo banner.

## How Users Change Branding

System Managers can open Desk:

`POS > POS Branding Settings`

From there they can update names, logos, PWA icons, colors, receipt text, install label, optional CSS, and demo banner settings.

## PWA And Manifest Impact

- `POS/index.html` points to `/api/method/pos_next.api.branding.get_pos_manifest`.
- The endpoint returns top-level `application/manifest+json` from `POS Branding Settings`.
- `id`, `start_url`, and `scope` remain `/pos`.
- Vite PWA static manifest injection is disabled so the runtime manifest is the source of truth.
- The generated service worker remains under `/assets/pos_next/pos/sw.js` and continues to control `/pos` through the existing registration flow.

## Workspace Impact

- Packaged workspace is now generic:
  - Name: `POS`
  - Label: `POS`
  - Title: `POS`
- Legacy Desk routes are redirected to the generic `pos` route.
- On `pos.trilogy-erp.com`, the old customer-specific workspace record was not deleted; it was hidden and made non-public so the visible workspace is `POS` only.

## Files Modified

- `POS/index.html`
- `POS/manifest.webmanifest`
- `POS/vite.config.js`
- `POS/src/main.js`
- `POS/src/App.vue`
- `POS/src/stores/branding.js`
- `POS/src/components/common/BrandingDemoBanner.vue`
- `POS/src/components/common/InstallAppBadge.vue`
- `POS/src/components/pos/POSHeader.vue`
- `POS/src/pages/Login.vue`
- `POS/src/pages/Home.vue`
- `POS/src/pages/POSSale.vue`
- `POS/src/utils/printInvoice.js`
- `POS/src/utils/errorHandler.js`
- `pos_next/api/branding.py`
- `pos_next/www/pos_manifest.py`
- `pos_next/hooks.py`
- `pos_next/public/js/desk_route_redirect.js`
- `pos_next/pos_next/doctype/pos_branding_settings/*`
- `pos_next/pos_next/print_format/pos_next_receipt/pos_next_receipt.json`
- `pos_next/pos_next/workspace/pos/pos.json`
- `pos_next/translations/ar.csv`

## Build And Test Results

- `npm run build`: passed using Node 20.20.2 from nvm.
- `bench build --app pos_next`: passed.
- Backup before migration: `sites/pos.trilogy-erp.com/private/backups/20260607_102113-pos_trilogy-erp_com-*`.
- `bench --site pos.trilogy-erp.com migrate`: passed.
- `bench --site pos.trilogy-erp.com clear-cache`: passed.
- `bench restart`: passed after Python changes.
- `/pos`: HTTP 200.
- Manifest endpoint: HTTP 200, `application/manifest+json`, returns `POSNext`, `POS`, `/pos` id/start/scope, and configured colors.
- `pos_next.api.branding.get_pos_branding_settings`: returns generic fallback settings from the new Single DocType.
- Service worker `/assets/pos_next/pos/sw.js`: HTTP 200 JavaScript.
- Supervisor: all `frappe-bench15` web, socketio, workers, and Redis processes running.

## Remaining Constraints

- Browser PWA/service-worker cache may require a hard refresh or reinstall prompt cycle for users who previously installed the old manifest.
- The legacy workspace internal database name still exists on the current site, but it is hidden/non-public and no longer the visible POS workspace.
- Customer-specific demo branding should be stored in `POS Branding Settings` site data, not in source logic.
