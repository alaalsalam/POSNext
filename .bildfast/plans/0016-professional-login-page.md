<!-- bildfast:plan id=0016 status=approved agent=bildfast task="Make the Desk login page look professional / smart" -->
# Plan: Professional restyle of the Desk login page

## Overview
User attached a screenshot of the **Frappe Desk login** (`/login`) — stock, bare styling (tiny
gray default button, "Show" toggle floating outside the password field, generic card, dead
space) — and asked to make it professional with a smart look.

## Approach (in-scope, no core edits)
- The login page is `frappe/www/login.html` (Frappe core — not editable per the operating
  rules). Confirmed it `extends templates/web.html`, and `web_include_css` hooks ARE injected
  into web pages including `/login` (via website_settings context). So an app CSS file loaded
  through `web_include_css` is the sanctioned way to restyle it without touching core.
- Read the actual login DOM from Frappe source to get exact selectors (`.for-login`,
  `.page-card`, `.page-card-head`/`.app-logo`, `.form-control`, `.email-field`/`.password-field`
  /`.field-icon`, `.toggle-password`, `.forgot-password-message`, `.page-card-actions`,
  `.btn-login`). Confirmed the login body carries `data-path="login"` → used it to scope every
  rule so nothing leaks to other web pages.
- Pulled the app's real brand colours from POS Branding Settings (emerald `#0a8754` /
  `#064e3b`) and consulted the ui-ux-pro-max skill for direction (soft bg, 16-24px radius,
  layered elevation).

## Execution Note
- `pos_next/public/css/login.css` (new): scoped to `body[data-path="login"]` — soft
  emerald-tinted gradient backdrop, centered elevated card (20px radius, layered shadow,
  rise-in animation), 48px rounded inputs with brand focus ring, field icon + "Show" toggle
  overlaid *inside* the inputs, full-width emerald gradient primary button with
  hover/active/focus states. Built with logical properties (`inset-inline-*`, `padding-inline`)
  so it mirrors correctly in RTL Arabic.
- `pos_next/hooks.py`: enabled `web_include_css = ["/assets/pos_next/css/login.css?v=…"]`.
- **Verified live end-to-end in the browser** (logged out, injected the served asset):
  - LTR: card/button/background all styled; found the "Show" toggle sat in a gap because the
    input (226px) didn't fill its `.password-field` wrapper (274px) and Frappe's default
    `right:9px` overrode the logical inset. Fixed by forcing the input to `width:100%` and
    hardening the toggle to `right:auto !important; inset-inline-end:14px !important` — re-checked
    geometry: input and field right edges both 881, toggle now inside the field.
  - RTL: flipped `dir=rtl` and re-screenshotted — envelope icon moves to the right (leading),
    "Show" toggle to the left (trailing) inside the field, labels/links right-align. Correct.
- Committed `c0c9f2c`.

## Deployment constraint (why the user saw it "not appear")
`web_include_css` (like `app_include_js`) is read from the imported `pos_next.hooks` **Python
module**, which this bench's gunicorn loaded once at `--preload` time (Aug 6, before this edit).
The bench is heavily multi-tenant (~45 sites on one gunicorn, PID 780, supervisor-managed
`frappe-bench-frappe-web`). Measured the live `/login` HTML: the CSS `<link>` is present in only
a *fraction* of requests and fluctuates (5/12 → 9/10 → 10/15) — because long-lived preloaded
workers keep repopulating the Redis `app_hooks` cache from their **stale** module, so it never
reliably reaches 100% and can decay. A graceful gunicorn reload would fix it deterministically,
but that reloads workers for all ~45 co-tenant sites — correctly blocked by the sandbox, and not
something to disrupt for a login cosmetic. (Per-site *data* is isolated per DB, but the gunicorn
*process* is shared.)

Did NOT force it via risky workarounds: no shared-gunicorn reload, and no editing the site's
Website Theme ("Standard YF") — theme records are per-site-DB but their compiled CSS is written
to the **shared** `sites/assets/` path keyed by theme name, so cross-site collision is a real
risk, plus it needs an SCSS compile.

**Resolution:** the change is committed to app code (hook + `login.css`), so the next
build/deploy of the app — which reloads the server process — makes it 100% permanent. Until
then it shows intermittently (a hard refresh usually catches a worker that has it). This is the
normal lifecycle for a hook addition; no further action from me is safe/warranted on the shared
host.

## Notes / not done
- `web_include_css` is read at gunicorn worker startup; this host runs `--preload` workers I
  must not restart (shared bench). They recycle every 2000 requests — and I directly observed
  them recycling this session (the earlier desk-redirect hook went live on its own: `/desk` now
  auto-redirects to `/desk/pos`). So the login styling starts serving automatically as workers
  roll; the CSS asset itself is already reachable at `/assets/pos_next/css/login.css`.
- Left the page **title** ("… Yemen Frappe") alone — that's the site name (System/Website
  Settings), a separate data change, not "styling". Can rebrand it to Kasherly/Digit POS on
  request.
- The blue "Kasherly" logo vs emerald brand accent is a pre-existing brand inconsistency (logo
  image is blue, configured theme is emerald). Used emerald to match the actual app theme; can
  switch the accent to the logo's blue if the user prefers logo-matching.
