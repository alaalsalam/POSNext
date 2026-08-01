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
reconciliation difference must be below 0.01. Payment percentages use submitted
non-return invoice `paid_amount`; outstanding credit is separate. Reports are read-only
and create no accounting entries, so cancellation and reversal follow the submitted or
cancelled Sales Invoice source without a secondary ledger.

ERPNext 16 stores Sales Invoice chronology in `posting_date` and `posting_time`. The API
sorts on those fields and constructs a response-only datetime for display; it never
queries a nonexistent `posting_datetime` column.

## Integrated reports

The in-POS dashboard passes the selected profile and resolved date range to all five
existing Desk reports: Sales vs Shifts, Cashier Performance, Payments and Cash Control,
Inventory Impact and Fast Movers, and Offline Sync and System Health.

## Acceptance data

`pos_next/tests/fixtures/reports_acceptance.json` is a non-posting demo dataset with cash,
card, credit, 15% tax, and a return. It never creates financial documents. The development
site also had 77 existing submitted POS invoices across seven profiles on 2026-08-01;
they were inspected read-only and no report flag was activated.

Acceptance checks include flag-negative manager/cashier calls, Profile A/Profile B and
company isolation, gross 345, returns 23, net 322, net before tax 280, tax 42,
outstanding 50, and single-locale Arabic/English RTL/LTR rendering.
