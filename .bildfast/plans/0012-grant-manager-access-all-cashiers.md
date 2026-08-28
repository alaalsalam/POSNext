<!-- bildfast:plan id=0012 status=approved agent=bildfast task="Grant Settings + catalog management access to all 15 demo cashiers" -->
# Plan: Give every demo cashier user Settings + catalog management access

## Overview
Direct follow-up: user asked to add the same access (Settings screen + catalog management) for
all the other cashier users, not just Phones.

## Plan
- @bildfast — data/config, no code: grant `POS Manager` role to the remaining 14 cashier
  users, verify each one end-to-end.

## Execution Note
Granted `POS Manager` (via `User.add_roles()`) to all 14 remaining users. 13 of 15 verified
`True` across the board immediately. **2 didn't** — `cafe@gmail.com` and
`perfumes@gmail.com.sa` still showed all three flags `False` after the grant, with `save()`
completing with no error.

Traced it properly instead of retrying blindly — stepped through `User.validate()`'s methods
one at a time on a loaded doc:
```
after append_roles("POS Manager")        -> role present
after move_role_profile_name_to_role_profiles -> role present
after populate_role_profile_roles         -> role GONE
```

**Root cause:** `User.populate_role_profile_roles()` (Frappe core) rebuilds `self.roles` to
exactly match the union of all assigned `role_profiles`, discarding anything else, but *only
when the user has at least one Role Profile assigned* (`if not self.role_profiles: return`).
Checked all 15 users' actual `User Role Profile` assignments (not just guessed from naming):
13 of them have **both** a narrow per-company profile (e.g. "POSNext Demo Cashier - Ph") *and*
a profile named **"Casher"** which already includes `POS Manager` in its role list — so the
union survives the rebuild. `cafe@gmail.com` and `perfumes@gmail.com.sa` only had their narrow
per-company profile, no "Casher" — so the rebuild silently stripped the manually-added role
every time, with no error.

**Fix:** assigned the same "Casher" Role Profile the other 13 already have to these 2 users
(`User Role Profile` child table), instead of fighting the role-profile system by re-adding the
role directly (which would just get stripped again on the next save by anyone). This is a
portability-safe, data-consistency fix — brings these 2 users in line with the other 13's
existing pattern rather than introducing a new one.

**Verified for all 15** (not just spot-checked): looped `get_pos_permissions()` as each
company's actual assigned user — `can_manage_feature_flags`, `can_create_items`,
`can_write_items` all `True` for every one.
