# Digit POS Feature Flag Foundation

## Scope

Milestone 0 provides four independent, POS Profile-scoped management flags:

| Feature key | POS Settings field | Default | Dependency |
|---|---|---:|---|
| `catalog` | `enable_catalog_management` | Off | None |
| `purchases` | `enable_purchases` | Off | None |
| `supplier_payments` | `enable_supplier_payments` | Off | Purchases |
| `pos_reports` | `enable_pos_reports` | Off | None |

Flags for later Master Plan milestones remain absent and therefore unavailable until
their own vertical slices define and pass acceptance. This avoids exposing placeholder
controls for capabilities that do not yet have a complete policy.

## Security and Access Model

- `POS Settings` remains readable by assigned cashiers because sales behavior must be
  bootstrapped into the POS session, but all mutation is manager-only.
- Only `System Manager`, `Sales Manager`, or `POS Manager` users with `POS Settings`
  write permission can save administrative settings or change the profile warehouse.
- `POS Cashier` has no `POS Settings` write permission.
- Profile assignment is mandatory for non-Administrator users. The shared access
  helper also evaluates document-level POS Profile and Company user permissions.
- Frontend visibility is only a convenience. `require_feature()` guards every
  catalog, purchase, supplier-payment, and in-POS report endpoint before its document
  permission checks, so a direct RPC call cannot bypass a disabled feature.
- Missing POS Settings, disabled POS Settings, missing profiles, and lookup failures
  resolve to denial or secure-off values.

## Persistence, Dependencies, and Audit

The flags are Check fields on profile-scoped `POS Settings`. Schema synchronization is
performed by the normal Frappe migration. Supplier Payments cannot be enabled unless
Purchases is enabled; disabling Purchases in the manager UI clears Supplier Payments,
and the document controller independently rejects an unsafe saved combination.

`POS Settings` has native `track_changes = 1`. Frappe Version records therefore retain
the actor, timestamp, and old/new values for all administrative changes, including
feature flags. After a successful transaction, the controller publishes
`pos_feature_flags_updated` with the changed values.

## Bootstrap, Cache, and Realtime Behavior

Bootstrap returns `feature_flags` once with the active session/profile data. POS module
visibility combines the persisted flag with the relevant ERPNext document permission.
On a realtime flag event for the active profile, the frontend:

1. invalidates bootstrap data;
2. reloads POS Settings;
3. invalidates and reloads the shared permission cache;
4. closes any management panel that is no longer authorized.

The manager Feature Flags tab uses translation keys and the active locale, so English
uses LTR text and Arabic uses translated RTL text without displaying both languages at
the same time. Controls retain touch-sized targets and a responsive one/two-column
layout.

## Data, Accounting, and Offline Effects

The foundation changes authorization and visibility only. It creates no accounting or
stock entries and has no queue, retry, conflict, reversal, or cancellation behavior.
Management capabilities remain online-only. Their financial and offline behavior must
be accepted within their respective milestones before activation.

## Development Migration and Rollback

Apply on a development site with:

```bash
bench --site digitpos.trilogy-erp.com migrate
```

For a safe operational rollback, turn all four flags off first. Reverting the milestone
commit and migrating removes the application metadata; retaining the four zero-valued
database columns temporarily is harmless. Never apply this procedure to production
without an explicitly approved release.

## Manual Acceptance

1. Open an assigned profile as a POS Manager and confirm the Feature Flags tab appears
   in POS Settings in English and Arabic.
2. Confirm all flags start off and all four management modules are hidden.
3. Attempt to enable Supplier Payments alone and confirm the dependency prevents it.
4. Enable one accepted flag, save, and confirm the corresponding module appears only
   when the manager also has its ERPNext permission.
5. In a second live session, confirm the module visibility refreshes after the realtime
   event without a page reload.
6. As a cashier, confirm Settings is hidden and direct calls to settings mutation and
   disabled management endpoints return PermissionError.
7. As a user assigned only to Profile A, confirm Profile B flags and endpoints are
   denied even if Profile B has the feature enabled.
8. Review the POS Settings Version timeline for actor, timestamp, and old/new values.
