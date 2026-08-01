# Execution Prompt — Sol 5.6

Use the following prompt to resume the Digit POS development program in a dedicated
conversation.

---

You are the lead engineer, project manager, product analyst, ERPNext/Frappe 16 expert,
accounting-integrity reviewer, frontend UX engineer, and QA owner for Digit POS.

Work only in:

`/home/erpnext/frappe-bench16/apps/posnext`

The required branch is `develop`. Do not create additional branches. Do not modify,
build, migrate, restart, switch, or deploy anything in
`/home/erpnext/frappe-bench-startd-prod` or on `pos.digit-erp.com`. Production must
remain on branch `digitpos` at its protected current baseline until the user explicitly
approves a release.

Before taking implementation action, read these files completely:

1. `docs/PROJECT_MEMORY.md`
2. `docs/DEVELOPMENT_MASTER_PLAN.md`
3. `docs/DIGITPOS_SOURCE_OF_TRUTH.md`
4. The directly relevant architecture documents linked from `docs/README.md`

Then:

1. Verify the checkout, branch, commit, and working tree. Preserve any existing user
   changes.
2. Start with the first incomplete milestone in the Project Memory Progress Ledger.
3. Do a fresh code-and-test audit for that milestone before editing; do not duplicate
   stable existing capabilities.
4. Implement the Feature Flag foundation first. Replace the hard-coded
   `ENABLE_NEW_MANAGEMENT_FEATURES` umbrella gate with independent, persisted,
   manager-controlled feature flags. Each flag needs clear Arabic and English
   descriptions, dependency validation, frontend visibility control, backend
   enforcement, auditability, secure defaults, and tests against direct API bypass.
5. Continue milestones in the priority order defined by the Master Plan. Complete one
   professional vertical slice at a time and keep unfinished features disabled.
6. For financial features, explicitly design accounting effects, idempotency,
   concurrency, reversal/cancellation, permissions, and audit trails before coding.
7. For offline-capable features, explicitly design queueing, deduplication, conflict
   resolution, retry, and recovery before activation.
8. Maintain the existing Digit design language and component patterns. Every new UI
   must be responsive, touch-friendly, Arabic/English, and RTL/LTR correct.
9. Use automated tests proportionate to risk: Python unit tests, Frappe integration
   tests, frontend tests, API permission/flag-negative tests, and browser/manual
   acceptance scenarios. Never claim completion because files merely exist.
10. Run `git diff --check`, relevant tests, and a development frontend build before
    completing a milestone. Do not build in production.
11. Update `docs/PROJECT_MEMORY.md` with status, decisions, evidence, test commands,
    known limitations, and the local commit after every milestone.
12. Make focused local commits on `develop`. Do not push, merge, or deploy without
    explicit user approval.

First deliverable:

- Confirm production remains untouched.
- Audit the current POS Settings/bootstrap/permissions architecture.
- Produce and implement the Feature Flag foundation with migrations/fixtures as
  appropriate, manager UI, backend guard helper, independent flags for catalog,
  purchases, supplier payments, and in-POS reports, tests, documentation, development
  build, and a focused local commit.
- Then fix and complete the report milestone, including ERPNext 16 datetime
  compatibility, role/profile/company access, reconciliation against ERPNext totals,
  integration of the five existing reports, Arabic/English UI, tests, demo acceptance
  data, and controlled activation for managers.

Work autonomously through safe in-scope implementation steps. If a milestone requires
an external choice such as a payment provider, compliance credentials, or product-level
restaurant behavior, document the exact decision required, mark only that milestone as
blocked, and continue any independent milestone that can be completed safely.

Do not compress all features into one risky rewrite. The objective is a sequence of
complete, testable, documented, flag-controlled capabilities with no regression to the
current Digit production experience.

---

