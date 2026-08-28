<!-- bildfast:plan id=0017 status=approved agent=bildfast task="Make all demo login accounts (usernames + passwords) log in correctly" -->
# Plan: Fix demo login accounts so every shop logs in

## Overview
User: "set the passwords and usernames so they all log in correctly." This is about the demo
account grid on the POS login page (`Login.vue`).

## Investigation (authoritative, from the DB)
- The 15 demo buttons carried these emails; cross-checked each against `User` + `POS Profile
  User`. **10 of 15 pointed at users that do not exist** (`support@trilogy-erp.com` — reused for
  BOTH الكافيه and البيتزا —, `trilogy@gmail.com`, `chocolates@trilogy.com.sa`,
  `flower@trilgy.com.sa`, `glasses@/hairdressing@/pharmacy@/restaurant@/toys@trilogy.com.sa`) →
  those buttons could never authenticate. The other 5 (gold, icecream, perfumes, phones,
  supermarket) were already correct.
- The real POS Profile user for each shop is `<name>@gmail.com` (all enabled), authoritative
  mapping taken from `POS Profile User` → `POS Profile.company`.

## Execution
1. **Passwords (site data):** set all 15 demo users' password to the shown `demo@2026` via
   `frappe.utils.password.update_password` (bypasses password-policy, fine for a demo whose
   password is printed on the login screen). Verified all **15/15 authenticate** with
   `check_password`.
2. **Emails (code):** corrected the 10 wrong emails in `Login.vue` `demoAccounts` to the real
   users (cafe@, chocolates@, Electrical@, flower@, glasses@, hairdressing@, pharmacy@, pizza@,
   restaurant@, toys@ — all @gmail.com). `bench build --app pos_next` (SPA static assets → live
   immediately, no worker-reload dependency).
3. **Verified end-to-end in the browser:** on `/pos/account/login` the grid now shows the
   correct emails; clicked الكافيه (`cafe@gmail.com`, previously broken) → logged in and the
   shift-opening dialog appeared ("الكاشير: Cafe"). Commit `e4c80f1`.

## Scope notes
- Did **not** touch `Administrator` or `ezadeen103@gmail.com` (the "محل الحصبة" / spare-parts
  shop) — the latter is a real non-demo shop (SAR) and isn't on the demo grid. Can set its
  password / add it to the grid on request.
- Passwords are site data (not shipped in code); the email corrections ship in `Login.vue`.
