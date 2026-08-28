<!-- bildfast:plan id=0019 status=approved agent=bildfast task="Grant users access to all 5 POS reports" -->
# Plan: Make all 5 POS reports openable by every POS user

## Overview
User: add report permission to the users so all reports show — they want to test every feature.

## Investigation
- Confirmed the report *logic* already authorizes POS users: `reporting_access.is_report_manager`
  includes `POS Manager`, and running each of the 5 report `execute()`s as chocolates@gmail.com
  succeeded (read on all 3 reference doctypes — Sales Invoice, POS Closing Shift, Offline Invoice
  Sync — plus the `enable_pos_reports` flag). Verified across **all 15 users**: all green.
- **But the 5 `Report` records' own role restrictions (Frappe's Desk report access control) were
  stale**: the live DB listed `POS User` and `Nexus POS Manager` (old/renamed roles) and did NOT
  include `POS Manager` — the role the demo users actually have. So clicking a report opened
  `/desk/query-report/...` and Frappe denied access (user has none of the report's roles), even
  though the report would have run.
- The shipped report **JSONs already list `POS Manager` correctly** — the live DB simply hadn't
  been synced to them.

## Execution
- Synced the 5 report records from their JSON via `frappe.reload_doc("pos_next", "report", …,
  force=True)` (the clean, shippable path — no code change needed since the JSON is already
  right; a fresh install/migrate is already correct). Stale `POS User` / `Nexus POS Manager`
  entries are gone; `POS Manager` is now present on all 5.
- **Verified for all 15 users**: each can now open all 5 Desk reports (role intersection), and
  the in-POS reports dashboard (`get_report_filters`) returns all 5 report links for a POS user.

## Notes
- Data-only change on this site (report role records brought in line with the shipped JSON);
  nothing to commit. Administrator and ezadeen103 (spare parts) untouched by intent.
- Combined with the earlier remount fix (0018), the POS "Reports" button shows and every report
  is now openable — ready to test.
