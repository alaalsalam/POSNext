# Digit POS Reports

## Activation and access

Reports are secure-off per POS Profile. A manager enables **In-POS Reports** in POS
Settings after assigning the intended managers to that profile. Every dashboard API
and all five Desk reports enforce the flag server-side. A request must include one POS
Profile; cross-profile aggregation is deliberately unsupported. Normal POS Profile,
Company, reference DocType, and User Permission checks remain authoritative.

Report viewers need a manager role (`System Manager`, `Sales Manager`, `POS Manager`,
`Accounts Manager`, `Stock Manager`, or `Item Manager`) and read permission for the
report's reference DocType. `POSNext Cashier` and `POS User` alone cannot view reports.

## Accounting model

Only submitted POS Sales Invoices (`docstatus = 1`, `is_pos = 1`) for the selected POS
Profile, its Company, and posting-date range are included. Sales are positive
`grand_total`; returns are the absolute value of negative return invoices; net sales are
the signed sum. The dashboard verifies:

`grand_total = net_total + total_taxes_and_charges`

`rounding_adjustment` is shown separately because ERPNext applies it when deriving
`rounded_total` from `grand_total`; it is not part of the equation above. The
reconciliation difference must be below 0.01.

Payment-method rows deliberately expose three values instead of calling gross receipts
"sales":

- **received**: absolute Sales Invoice Payment tender on non-return invoices;
- **refunded**: absolute tender on return invoices;
- **net**: received minus refunded for that method, before unallocated change.

At period level, `tender_total = received_total - refunded_total` and
`net_total = tender_total - change_total`. ERPNext does not identify which payment mode
funded `change_amount`, so change is shown once at period level and is not guessed into a
method. `tender_difference = tender_total - signed paid_amount`; this must be below 0.01
to claim tender reconciliation.

The separate invoice-balance equation is:

`rounded_total = paid_amount + outstanding_amount + write_off_amount - change_amount`

All terms are signed and include returns. `settlement_difference` and
`settlement_reconciled` report this equation honestly. Current ERPNext outstanding can
change after later allocations; therefore a non-zero difference is surfaced for review
rather than hidden. On the audited `الجوالات` dataset, tender reconciles but three
historical invoices produce a 1,050.00 balance difference because their current negative
outstanding no longer matches the original POS tender snapshot.

Reports are read-only and create no accounting entries, so cancellation and reversal
follow the submitted or cancelled Sales Invoice source without a secondary ledger.

ERPNext 16 stores Sales Invoice chronology in `posting_date` and `posting_time`. The API
sorts on those fields and constructs a response-only datetime for display; it never
queries a nonexistent `posting_datetime` column.

Date-only Sales Invoice filters remain inclusive. Filters applied to Datetime fields
(`period_start_date`, `period_end_date`, and `synced_at`) use a half-open range:
`>= from_date 00:00:00` and `< day_after(to_date) 00:00:00`. This includes the final
microsecond of the requested end date. Inventory depletion uses inclusive calendar days
(`date_diff + 1`), so a one-day report divides by one.

## Integrated reports

The in-POS dashboard passes the selected profile and resolved date range to all five
existing Desk reports: Sales vs Shifts, Cashier Performance, Payments and Cash Control,
Inventory Impact and Fast Movers, and Offline Sync and System Health.

Payments and Cash Control fetches transaction counts and bank deposits in two batch
queries after the base shift query. Each shift receives `bank_deposit_amount = 0` and
`deposit_date = null` when no submitted Bank Deposit is linked. Dynamic payment columns
use deterministic ASCII prefixes plus a Unicode-aware hash, preventing collisions for
Arabic, punctuation, symbols, or case-only differences.

## Acceptance data

`pos_next/tests/fixtures/reports_acceptance.json` is a non-posting demo dataset with cash,
card, credit, 15% tax, and a return. It never creates financial documents. The development
site also had 77 existing submitted POS invoices across seven profiles on 2026-08-01;
they were inspected read-only and no report flag was activated.

Acceptance checks include flag-negative manager/cashier calls, Profile A/Profile B and
company isolation, gross 345, returns 23, net 322, net before tax 280, tax 42,
outstanding 50, and single-locale Arabic/English RTL/LTR rendering.

## Repeatable backend test command

From the app checkout, run:

```bash
../../env/bin/python run_reports_tests.py
```

The runner initializes the development Frappe site, loads only the three POS report test
modules, rolls back the database, and returns exit code `1` if any assertion fails. It
does not generate ERPNext test records or delete/modify user data. Standard
`bench run-tests` remains blocked before selected modules by ERPNext's duplicate
`Standard Buying` bootstrap defect; no data is removed to bypass it.
