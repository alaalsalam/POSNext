<!-- bildfast:plan id=0003 status=approved agent=bildfast task="Fix the broken POS Workspace reinstall patch + purge the legacy duplicate workspace, in app code" -->
# Plan: Fix the POS Workspace install/cleanup patch (in app code, not a DB hack)

## Overview
User's standing rule: `pos_next` is the single source of truth — no fix may depend on a
one-off database tweak on this dev/demo site; everything must ship as app code so a fresh
install on a client site ends up correctly configured too. Current priority #2 is
"install the POS Workspace inside the app properly."

**Root cause found (confirmed by reproducing it locally, no guessing):**
`pos_next/patches/v1_7_0/reinstall_workspace.py` is the patch responsible for (re)installing
`workspace/pos/pos.json` on every site (fresh installs and upgrades alike). Its
`_load_workspace_data()` helper has a bug on its last line:

```python
return workspace_data[0]   # BUG: workspace_data is already a dict here, not a list
```

`pos.json` is a plain JSON *object* (not a list), so after `json.loads()` this line does
`some_dict[0]`, which raises `KeyError: 0`. I reproduced this locally with the real file —
confirmed. Because this raises uncaught, the patch's actual job (delete any old-named
workspace doc, install the current one fresh) never completes successfully on any site.

**Why this matters right now, concretely (not hypothetical):** `pos.yemenfrappe.com` (this
project's site) currently has **two** workspaces under the "POS Next" module:
- `POS` — the current one, shipped by `workspace/pos/pos.json`.
- `POSNext` — an orphaned leftover. Git history confirms the app used to ship
  `workspace/posnext/posnext.json` (name `POSNext`) and it was replaced by the current
  `workspace/pos/pos.json` (name `POS`) in a later commit. The old file was deleted from the
  app, but the patch meant to delete the old *database record* on upgrade has been silently
  broken since — so the stale `POSNext` workspace still shows up in the sidebar today, and
  would keep showing up on any other existing install that upgrades through this patch.

## Plan
- @bildfast (small, targeted, contained to the two patch files below — no sub-agent needed)
1. Fix the one-line bug in `pos_next/patches/v1_7_0/reinstall_workspace.py`
   (`_load_workspace_data`): return `workspace_data`, not `workspace_data[0]`. This makes the
   existing patch actually work — going forward it correctly reinstalls `POS` from the JSON
   file on every site (fresh installs included).
2. Frappe patches are one-shot and immutable once shipped — sites that already "ran" the
   broken version (this dev site has a `Patch Log` row for it) won't automatically re-run it
   just because the code changed. So the leftover `POSNext` record needs a **new** patch
   (added under the existing `v2_0_0` bucket, next to `remove_custom_company_fields`) that
   explicitly removes known legacy workspace names (`POSNext`). This is registered in
   `patches.txt` like every other patch — it runs automatically on this dev site's next
   migrate *and* on any already-upgraded client site, and is a safe no-op on a truly fresh
   install (nothing to delete).
3. Test before calling it done:
   - Re-run the fixed JSON-loading logic locally against the real `pos.json` → must return
     the dict without raising (base scenario).
   - Invoke the new cleanup patch's `execute()` directly via `bench execute` on this dev site
     (not `bench migrate`) to verify it removes `POSNext` and is idempotent (running it twice
     is a harmless no-op — required for patches in general).
   - Confirm the `POS` workspace itself (links, roles) is unaffected/still correct after the
     `reinstall_workspace` fix reinstalls it.
   - Confirm no other doctype/data is touched (Workspace deletion only removes the sidebar
     entry — no linked transactional data).

## Execution Note
Executed after the user asked (in a later turn) to "add the workspace with reports and
everything POS-related" — investigated first and found the workspace was never actually
missing content: `workspace/pos/pos.json` already had all 5 reports plus Sales/Customer/Item/
Warehouse/Settings/Offers links, correctly synced to the live site's "POS" Workspace record.
The real problem was exactly what this plan diagnosed: the orphaned "POSNext" duplicate
(`sequence_id: 0`, i.e. sorted *before* "POS") was almost certainly what the user was actually
seeing/clicking into, since it's thinner (no reports section header naming, fewer links) and
comes first in the sidebar.

- Fixed the one-line bug in `reinstall_workspace.py` as planned.
- Added `v2_0_0.cleanup_legacy_workspace`, registered in `patches.txt`.
- Did not run `bench migrate`. Instead, on this dev site, invoked both patch `execute()`
  functions directly via `bench execute` (same narrow-action pattern used throughout this
  session): `reinstall_workspace.execute()` (confirmed it now completes without the former
  `KeyError`, and correctly re-inserts "POS" — Frappe's own `developer_mode` auto-export
  rewrote `pos.json` into its canonical format as a side effect of that real `insert()`, content
  unchanged) then `cleanup_legacy_workspace.execute()` (confirmed "POSNext" is gone — queried
  `Workspace` for module "POS Next" before and after; only "POS" remains). Ran the cleanup patch
  a second time to confirm it's a safe no-op (idempotent), per the plan's own test checklist.
- "POS" now sorts first among this site's workspaces (`sequence_id: 1`, right after Frappe's
  own default-first slot) with no competing duplicate.

Committed as `fix: repair broken workspace-reinstall patch and purge the orphaned POSNext
workspace` (commit `20ef2d0`).
