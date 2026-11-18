# REVIEW

## Awaiting review

- [ ] Excel backup controls in Account Settings
  - **Delivered:** Replaced the exposed native file picker with matching Export Excel and Import Excel buttons in `frontend/src/pages/Settings.tsx` and `frontend/src/index.css`.
  - **Evidence:** `npm run build` and `npm run lint` passed; desktop and mobile screenshots showed no overflow, and the Import Excel button opened the file chooser in an isolated browser check.
  - **Review focus:** Confirm the button appearance and placement in Account Settings on desktop and mobile.

- [ ] Inline transaction editor
  - **Delivered:** Editing a transaction now opens its form directly below that transaction in `frontend/src/pages/PiggyBankView.tsx`, with responsive styles in `frontend/src/index.css`.
  - **Evidence:** Frontend build and lint passed; desktop and mobile checks confirmed the form appears immediately after the selected row, and a PiggyBank transfer remains editable through its paired transaction.
  - **Review focus:** Confirm that editing long transaction lists feels clear on desktop and mobile.

- [ ] Transaction list keeps its place and formats amounts clearly
  - **Delivered:** Saving or deleting a transaction refreshes the PiggyBank view without the full-page loader, so the scroll position is kept. Amounts show the sign before the currency symbol (`-S$6.42`, `+S$10.00`) through a shared `formatMoney` in `frontend/src/utils/money.ts`, also used for Dashboard balances. Row edit and delete buttons are vertically centered.
  - **Evidence:** `npm run build` and `npm run lint` passed.
  - **Review focus:** Edit a transaction far down a long list and confirm the page stays in place; check amount signs and button alignment on desktop and mobile.

- [ ] Ludwig ledger description and category cleanup
  - **Delivered:** Through SQLAlchemy, for Ludwig only: Zensho descriptions → `Sukiya` (26); `UOB interest`, `Interest Credit`, and `Bonus Interest` → `Interest` (18); removed `(Kopitiam)` from `Lunch`, `Dinner`, and `Coffee` (181); `Supper (Hanbaobao)` → `Supper (McDonalds)` (57). Added `Software` and `Utilities` categories and moved 20 rows from `Others`: ZYM Mobile Fee → `Utilities` (11), Anthropic/Claude/Google AI/Gemini → `Software` (8), Google Twitch → `Entertainment` (1).
  - **Evidence:** Each change was compared against a pre-change backup in `data/backups/`: row count unchanged and no changes outside the targeted field. Per-row before/after records are in `data/*.json`.
  - **Review focus:** Spot-check the renamed descriptions and new categories in the app. Transaction 827 (an interest credit) is still categorized as `Savings`.

- [ ] Category consolidation and retired `Transfer` category
  - **Delivered:** `backend/app/domain/category_names.py` maps `Other` and `Transfer` to `Others`, and `Withdraw`/`Withdrawal` to `Withdrawals`, in transaction create/edit, category create/rename, and Excel import. `backend/consolidate_categories.py` (dry run by default, `--apply`) rewrote existing data: 12 transactions (10 bank transfers `Transfer` → `Others`, 1 `Other` → `Others`, 1 `Withdrawal` → `Withdrawals`) and Ludwig's category list (`Withdraw` renamed; `Other`, `Transfer`, `Withdrawal` removed as duplicates). PiggyBank transfers keep their system `Transfer In`/`Transfer Out` labels.
  - **Evidence:** `pytest tests -q` passed (42); new tests in `backend/tests/test_category_names.py` cover bank transfers, PiggyBank transfers, Excel import of old spellings, and idempotent consolidation. Live data compared against `data/backups/piggynest-before-category-consolidation-*.db`: only categories changed; a second run found nothing.
  - **Review focus:** The fallback is `Others` (the earlier TODO decision said `Other`; changed to match existing data and the owner's request).

- [ ] Transactions per page setting
  - **Delivered:** `users.transactions_per_page` (10, 20, 50, or 0 for all; default 20), added by the startup schema upgrade and saved through `PUT /api/v1/auth/me`. Account Settings has a Display section; the PiggyBank transaction list pages client-side with previous/next controls. Charts still use every transaction.
  - **Evidence:** Backend test for per-user values and rejection of other sizes; `npm run build` and `npm run lint` passed. Not yet checked in a browser.
  - **Review focus:** Change the setting, open a long PiggyBank, and check paging on desktop and mobile. The CLI does not read this setting yet.

- [ ] Per-user date format in the browser and CLI
  - **Delivered:** `users.date_format` (`YYYY-MM-DD` default, `DD/MM/YYYY`, `MM/DD/YYYY`), saved through `PUT /api/v1/auth/me`; the API still sends and accepts ISO dates. Account Settings > Display has the format choice with a live example (and the label spacing fix). The PiggyBank list shows dates in that format, and the transaction form takes a typed date in it, rejecting mismatches with a message naming the format. `cli.py` reads the format after login and uses it in add/edit prompts and parsing; Add Transaction now also asks for an optional date.
  - **Bug fixed along the way:** The editor used `toISOString()` on API dates, so in UTC+8 it prefilled the previous day and saving moved the transaction back one day. Dates are now handled as calendar dates (`frontend/src/utils/dates.ts`) and sent as `YYYY-MM-DDT00:00:00`.
  - **Evidence:** `pytest tests -q` passed (45), including per-user API tests and CLI prompt/parse/reject tests; parser checked in Asia/Singapore and America/Los_Angeles; `npm run build` and `npm run lint` passed. Not yet checked in a browser.
  - **Review focus:** Switch formats, edit a transaction, and confirm its date stays the same; check the Display section and the form on desktop and mobile.

- [ ] Cleaner PiggyBank balance chart
  - **Delivered:** The analytics line in `frontend/src/pages/PiggyBankView.tsx` plots one point per calendar day (end-of-day balance, or that day's money in/out), on a true time axis with month ticks (`YYYY/MM`, at most ~8), as a step area for the balance with a light gradient fill. Per-point dots are gone; a single dot appears on hover. Tooltip dates use the account date format and amounts use `formatMoney`.
  - **Evidence:** `npm run build` and `npm run lint` passed. Not yet checked in a browser.
  - **Review focus:** Open EZLinkSG60 analytics; the gap with no data in December 2025 should now show as a flat stretch, and labels should not overlap on desktop or mobile.

- [ ] EZLinkSG60 commute estimates and November statement
  - **Delivered:** Lost old card: the 2025-08-15 and 2025-08-22 top-ups (S$30) went to a card that was later lost, so three school commutes (2025-08-15/18/22) and a `Lost EZ-Link card: remaining balance` write-off (S$18.94, 2025-08-24) now use them up; the new card starts on 2025-08-25 with S$14.40. Estimated daily commute rows (`Commute: work/school`, `Trip: …`) from 2026-01-12 to 2026-11-04 were rebuilt from the owner's schedule so the balance stays between S$0 and S$40. Actual statement taps cover 2026-11-05 to 2026-11-18 (25 rows, bus fare refunds netted into each bus ride).
  - **Evidence:** Balance is S$12.62, matching the card on 2026-11-18; running balance stays between S$0.00 and S$38.97 from 2025-08-15 on; end of 2026-11-04 is S$22.12 as the statement implies. Backups are in `data/backups/`; row IDs to undo are in `data/ezlink-rebuild-*.json` and `data/ezlink-statement-*.json`.
  - **Review focus:** The old-card rows and the January–October 2026 rows are estimates, not statement data. The write-off could instead be more old-card commutes if those days are remembered.
