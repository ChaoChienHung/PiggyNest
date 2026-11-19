# REVIEW

## Awaiting review

- [ ] Transaction Type filter, keyword search, and bulk actions (change category & bulk delete)
  - **Delivered:**
    - Added a multi-select **Types** filter (`Expense`, `Income`, `PiggyBank Transfer`, `Bank Transfer Out`, `Bank Transfer In`, plus legacy types when present) using the shared `FilterPicker`, and a **Search** input matching description, category, `#ID`, and amount in `frontend/src/pages/PiggyBankView.tsx`. `Clear filters` resets Type, Category, Search, Sort, Date range, and selection.
    - Added atomic backend endpoints `POST /api/v1/transactions/bulk-category` and `POST /api/v1/transactions/bulk-delete` in `backend/app/api/v1/transactions.py` (user-scoped; bulk category normalizes category names and rejects PiggyBank transfers whose directional labels are fixed; bulk delete atomically removes both sides of any PiggyBank transfer).
    - Added a `Select` / `Done` toggle button beside `Add Transaction` so checkboxes stay hidden in normal browsing; entering Select mode reveals row checkboxes, page select-all, "Select all matching", and the themed bulk action bar in `frontend/src/pages/PiggyBankView.tsx` and `frontend/src/index.css` (with explicit PiggyBank transfer pair warning in the delete confirmation modal and mobile grid alignment). Also fixed the missing `.block` CSS utility so the Dashboard `Create PiggyBank` form stacks the `Currency` label cleanly above its dropdown.
  - **Evidence:** Backend pytest suite passed (including new bulk category, bulk delete, transfer pair, bank transfer, and cross-user isolation tests in `backend/tests/test_transactions.py`); `cd frontend && npm run build && npm run lint` passed.
  - **Review focus:** Combine Types, Categories, Search, and Date filters on a PiggyBank; select multiple rows to change category or delete (including a PiggyBank transfer to verify the pair warning and atomic balance update).

- [ ] Upgraded PiggyNest browser favicon (Option C: dark-plum & coral-pink geometric piggy with gold coin)
  - **Delivered:** Replaced the plain line-art favicon in `frontend/public/piggynest.svg` with the owner-selected Option C design: a dark-plum gradient squircle (`#5c4760` → `#352838`) with a coral-pink piggybank silhouette and gold coin accent for crisp readability at 16px browser tab sizes on both light and dark themes.
  - **Evidence:** `cd frontend && npm run build && npm run lint` passed; `dist/piggynest.svg` reflects the updated asset.
  - **Review focus:** Refresh the browser tab (hard refresh if cached) and confirm the icon looks sharp in light and dark tab bars.

- [ ] Batch 1 engineering optimizations (Alembic migrations, config & legacy cleanup, frontend code splitting, and docs)
  - **Delivered:**
    - Added Alembic (`alembic>=1.13.0,<2.0.0`) with `backend/alembic.ini`, `backend/migrations/env.py` (`render_as_batch=True`), baseline revision `0001_initial_schema`, and `backend/app/db/migrations.py` (`run_migrations`) replacing startup `create_all` and inline `ALTER TABLE` blocks while safely bridging pre-Alembic SQLite databases without data loss. Removed obsolete `backend/migrate_db.py` and `backend/migrate_db_v3.py`.
    - Consolidated configuration in `backend/app/core/config.py` around environment variables and `backend/.env` (removing unused `PyYAML`/Google Drive settings, dead `backend/app/core/config.yaml`, four unimported legacy CSV/pandas domain modules, and the empty root `requirements.txt`).
    - Split all frontend routes and `SettingsDialog` in `frontend/src/App.tsx` with `React.lazy` and `Suspense`, shrinking the initial entry JS chunk from `756.20 kB` (`231.04 kB` gzip) to `275.87 kB` (`91.10 kB` gzip) (-63.5% raw / -60.6% gzip) and eliminating the Vite >500 kB chunk warning.
    - Documented background, rationale, benefits, impact, and measured results in `docs/engineering-optimizations.md` and updated `docs/backlog.md`.
  - **Evidence:** Backend pytest suite passed (72 tests, including 3 new migration tests in `backend/tests/test_migrations.py` covering fresh DBs, pre-Alembic legacy DB bridging, and downgrade/re-upgrade round-trip); `cd frontend && npm run build && npm run lint` passed with zero warnings.
  - **Review focus:** Review `docs/engineering-optimizations.md`, start the app against your local database to confirm seamless Alembic stamping/startup, and click through Dashboard, PiggyBank, Reports, Analysis, and Settings to confirm smooth lazy-loaded route transitions.

- [ ] Transaction Categories filter follows the shared picker behavior
  - **Delivered:** The PiggyBank transaction filter labels Categories above its field. Every category is checked by default when the field reads All; `Select all` checks every option and `Clear` unchecks every option. Clearing categories shows no matching transactions, while the page's `Clear filters` button restores the default all-selected state. The shared picker keeps search, outside-click dismissal, and the existing scrollable option list.
  - **Evidence:** Frontend build and lint passed; `git diff --check` passed. Browser access was unavailable in this session.
  - **Review focus:** Open a PiggyBank with several categories, confirm all boxes start checked, clear and reselect them, then check the Categories label and menu placement beside Sort by, Order, and the date fields on desktop and mobile.

- [ ] CLI in-process FastAPI fallback and full web feature parity
  - **Delivered:** `cli.py` now uses `httpx` (removing the extra `requests` install) and selects its transport automatically: HTTP when `PIGGYNEST_API_URL` points to a remote API or the local backend is running on `127.0.0.1:8000`, and in-process `TestClient` fallback when no local server is started. Brought CLI to parity with the web app: Register & Account Recovery, Total Net Worth in `display_currency`, category menu + inline creation in Add Transaction, updated types (`expense`, `income`, `transfer_out`, `transfer_in`), View Transactions, Delete Transaction (with PiggyBank transfer pair warning), cross-currency transfer creation & counterpart editing, Category CRUD, Numeric Reports (daily/monthly/yearly, excluding PiggyBank transfers from income/spending), PNG chart export to `data/diagram/` (balance, monthly cashflow, expense breakdown via `matplotlib`), Settings & NTD exchange rates, Excel backup export/import, and Account Deletion. Consolidated CLI tests into `backend/tests/test_cli.py` (removing `test_cli_edit.py`). Updated `README.md`, `docs/architecture.md`, and `docs/data-sync.md`.
  - **Evidence:** Backend test suite passed (69 tests, including 22 CLI tests in `backend/tests/test_cli.py` covering transport fallback, remote safety, auth/register, PiggyBank CRUD & Net Worth, category menu & CRUD, add/list/edit/delete transactions, same/cross-currency transfers, numeric reports, matplotlib PNG chart export, settings/rates, and Excel backup round-trip); verified live on Bob and real in-process FastAPI startup against an isolated temporary SQLite database.
  - **Review focus:** Run `backend/venv/bin/python cli.py` both with and without `uvicorn` running to confirm the displayed mode (`HTTP API` vs `Local in-process API`), try transfers, reports, settings/backup, and inspect generated PNGs under `data/diagram/`.

- [ ] Side-by-side analytics filters and explicit category selection
  - **Delivered:** Combined Graph Analysis places PiggyBanks and Categories controls side by side on desktop and labels each field above its value. The shared filter control gives Reports the same visible labels. Category filters on both analysis views and Reports now start with every available category checked. `All categories` checks all; `Clear` unchecks all and shows a select-category prompt. Changing the selected PiggyBanks resets categories to all of the newly available options. An open filter's glass panel now rises above adjacent panels so the Categories menu stays visible over PiggyBank Analytics.
  - **Evidence:** Frontend build and lint passed; `git diff --check` passed. Visual behavior awaits review.
  - **Review focus:** Open both menus on desktop, check two-column spacing and labels, confirm the single-bank Categories menu overlaps PiggyBank Analytics without being covered, then try All categories, Clear, and individual checkboxes in combined Graph Analysis, single-bank Graph Analysis, and Reports.

- [ ] Graph Analysis controls and persistent pig menu
  - **Delivered:** PiggyBank Graph Analysis uses Income and Expenses labels without the obsolete Deposit/Withdrawal wording. Both combined and single-bank Graph Analysis pages have searchable category filters that apply to their charts independently of transaction-list filters. The pie chart's category details control sits below the chart and reads `Category Breakdown`. The fixed pig menu remains available on Dashboard, PiggyBank, Graph Analysis, and Reports, including while add/edit forms are open; the existing desktop gutter continues to reserve space beside content.
  - **Evidence:** Frontend build and lint passed; `git diff --check` passed. Visual behavior awaits review.
  - **Review focus:** Try multiple categories and clear the selection in both analysis views; check the pie details button beneath the chart and FAB placement on forms, analysis, and reports.

- [ ] Numeric chart and report dates, and simpler transaction types
  - **Delivered:** PiggyBank Monthly Summary labels use numeric months (`YYYY/MM` for the year-first setting, `MM/YYYY` for either day-first setting). PiggyBank chart ticks and combined chart axes/tooltips follow the account date format; Reports follows it for daily and monthly periods. Monthly Summary groups by the stored calendar date, independent of browser language and time zone. Deposit and Withdrawal are absent from the new-transaction Type list; existing transactions with those types remain editable under their original type.
  - **Evidence:** Frontend build and lint passed; `git diff --check` passed. Visual behavior awaits review.
  - **Review focus:** Switch through all three Settings date formats and compare the PiggyBank chart, Monthly Summary, combined charts, and Reports. Open an older Deposit or Withdrawal to verify its type remains selected when editing.

- [ ] Custom calendar and dedicated analytics navigation
  - **Delivered:** All date fields keep typed entry and now open an app-styled calendar from an icon inside the input. The calendar renders above surrounding panels, chooses its position from available viewport space, and has direct month and year selection. The fixed, larger FAB uses a line-art piggy-bank icon, opens its centered icon links on hover or click, and sits about 10px outside the white content area on desktop without covering transaction actions. Graph Analysis has its own route for the combined Dashboard and individual PiggyBank charts; the PiggyBank ID is passed into the analysis view so its data request runs; Reports stays on its own route. Both pages include a back link to the originating Dashboard or PiggyBank.
  - **Evidence:** Frontend build and lint passed after the FAB and loading fixes. The earlier browser control session was unavailable and the current Python environments lack Playwright, so visual behavior remains for human review.
  - **Review focus:** Check the calendar above and below fields, quick month/year selection, choosing a day, typed dates, FAB hover and its 10px gutter beside the transaction actions, PiggyBank Graph Analysis loading, and each back link on desktop. Mobile layout polish remains deferred in `TODO.md`.

- [ ] Smooth balance chart lines
  - **Delivered:** PiggyBank and combined Dashboard balance charts use a monotone curve through the same daily or period totals, replacing the previous staircase rendering. Income and expense data and stored transactions are unchanged.
  - **Evidence:** Frontend build and lint passed.
  - **Review focus:** Compare the curve and tooltip values for a PiggyBank with several balance changes, and check the combined chart on Graph Analysis.

- [ ] Close PiggyBank category filters
  - **Delivered:** The Categories menu closes when clicking outside or pressing Escape.
  - **Evidence:** An earlier isolated desktop browser check verified both dismissal methods.
  - **Review focus:** Try a long category list and confirm the menu closes without changing selections.

- [ ] Desktop filter menus and transaction Type width
  - **Delivered:** The PiggyBank Categories menu now opens below its field without stretching the filter row. Dashboard and Reports use compact searchable PiggyBank/category menus with fixed-height scrolling lists; bulk actions sit inside the menus as themed buttons. The transaction Type control fills its grid column to reduce the visual gap before Date.
  - **Evidence:** Frontend build/lint passed. An isolated desktop browser check with eight PiggyBanks and 30 categories confirmed Reports filter height stays fixed, the list scrolls and searches, bulk actions work, and Type and Date controls both measure 263px wide. Dashboard filter actions and Reports preselection still worked in a second browser check.
  - **Review focus:** Open the affected filters and transaction form on desktop. Mobile polish is deferred in `TODO.md` at the owner's request.

- [ ] Fixed-rate currency display
  - **Delivered:** Each user has a display currency and NTD reference rates in Settings. The owner-selected default is `1 SGD = 24.00 NTD` for new accounts; startup fills only missing SGD rates for existing accounts. Rates accept positive values with at most four decimals and show their last update date. Conversion through NTD changes display figures only; missing rates show a Settings prompt.
  - **Evidence:** Backend suite passed (52), including per-user isolation, input validation, account defaults, and an idempotent backfill that preserves custom rates. Bob's local profile showed its new 24.00 rate. Frontend build/lint and conversion tests passed; isolated desktop/mobile browser checks changed 24 to 25 and observed immediate updates in net worth, analytics, and Reports without database writes.
  - **Review focus:** Check Settings rate editing and hover explanations on converted figures; try an unconfigured currency to confirm the rate-needed message.

- [ ] Combined Total Net Worth card
  - **Delivered:** The Dashboard sums converted PiggyBank balances into one selected-currency amount, lists up to five currencies with original amounts and shares, and remembers the per-user hide/show setting.
  - **Evidence:** Frontend build/lint passed. Isolated desktop/mobile browser checks compared the total to a two-currency fixture, changed the rate, and confirmed the hidden amount persisted after reload with no horizontal overflow.
  - **Review focus:** Check the card with your real balances, especially the top-currency order and percentage shares.

- [ ] Combined Dashboard analytics
  - **Delivered:** Balance, income/spending, money-flow, and category charts combine selected PiggyBanks in the display currency. Bank chips, Select all/Clear all, and a date range apply across chart metrics; PiggyBank transfers affect balance but not income or spending.
  - **Evidence:** Frontend build/lint passed. Isolated 1280px/390px browser checks exercised chip selection, empty state, metric switching, live rate updates, and no horizontal overflow. Ledger calculation tests cover PiggyBank and bank transfers and conversion through NTD.
  - **Review focus:** Compare the ending balance with Total Net Worth when all banks are selected and no date range is active; try chip and date filters on a real ledger.

- [ ] Numeric Reports view
  - **Delivered:** Dashboard and PiggyBank links open daily, monthly, and yearly income, spending, and net-change summaries with totals, averages, minima/maxima and their periods, and transaction counts. The PiggyBank link preselects that bank. Bank/category/date/currency filters and hidden-amount preference apply; zero-activity periods count in averages.
  - **Evidence:** Frontend build/lint passed. Calendar tests cover empty days, month and year boundaries; ledger tests cover transfers. Isolated desktop/mobile browser checks confirmed figures, preselection, live rate updates, and no horizontal overflow.
  - **Review focus:** Compare a small date range against hand calculations and check how zero periods and transfers appear.

- [ ] Direct PiggyBank transaction page navigation
  - **Delivered:** Up to five numbered page buttons follow the current page, shifting back at the end, with an ellipsis and last-page shortcut. Previous/Next and a labeled page-number field support direct navigation; invalid or out-of-range entries show an error without moving the page.
  - **Evidence:** Frontend build and lint passed. An isolated browser check with 61 Bob-shaped transactions and ten rows per page exercised numbered links, Enter, empty/non-integer/out-of-range errors, and 1280px/390px widths. The check made no database changes; an earlier API-based check cleaned all 61 temporary Bob transactions and restored the original page size.
  - **Review focus:** Try a long real PiggyBank list and confirm the page links and input feel clear on desktop and mobile.

- [ ] Empty transaction descriptions and Qashier merchant labels
  - **Delivered:** Cleaned all 111 null-like transaction descriptions across the local database through SQLAlchemy. Specific categories supply most labels; IDs 367, 498, and 539 use generic type labels because no merchant or source is recorded. Renamed 3 `Qashier-MUYOO` entries to `Bread` and 20 `Qashier-AGZ Food` entries to `Lunch` or `Dinner` using other same-day meal descriptions; when neither existed, used the owner-approved arbitrary choice.
  - **Evidence:** Backup and per-ID before/after audit are in ignored `data/backups/piggynest-before-description-cleanup-*.db` and `data/description-cleanup-*.json`. Comparing 2,077 rows before and after found 134 Description changes and no changes to other transaction fields. Backend tests passed (46); the cleanup is idempotent in its test.
  - **Review focus:** Spot-check the three generic descriptions and the inferred meal labels, especially dates where neither meal was already recorded.

- [ ] PiggyNest browser icon and metadata
  - **Delivered:** Replaced the Vite favicon with a scalable pig icon in `frontend/public/piggynest.svg`; updated the browser title, description, and theme color in `frontend/index.html`; removed the Vite asset.
  - **Evidence:** Frontend build and lint passed; the production output contains the new icon and no `vite.svg`.
  - **Review focus:** Check the browser tab icon at normal and high-density sizes on desktop and mobile.

- [ ] Floating Additional Tools button
  - **Delivered:** The Dashboard and PiggyBank view share a fixed pig button that reveals a Graph Analysis action on hover, keyboard focus, or tap. The action toggles the existing charts; Escape returns focus to the pig button.
  - **Evidence:** Frontend build and lint passed. A mobile-sized browser check opened the action by tapping the pig button. The button is removed while an add or edit form is open so it cannot cover form buttons.
  - **Review focus:** Check placement and opening on desktop and mobile, including touch and keyboard access.

- [ ] Cross-currency PiggyBank transfers with dates
  - **Delivered:** Same-currency transfers still use one amount; cross-currency transfers require actual sent and received amounts, with an optional shared date and an implied-rate display. Editing either leg can update its own amount and the counterpart amount independently while keeping direction and shared transaction ID. Excel import validates same-currency equality and cross-currency signs; docs and `AGENTS.md` reflect the new rule.
  - **Evidence:** Backend suite passed (50), including pair creation, editing, account isolation, backup round-trip, bank transfers, and deletion. Frontend build and lint passed. Bob-only desktop/mobile browser checks created an SGD → NTD transfer and edited it on mobile to `-S$12` / `NT$276`, with no horizontal overflow.
  - **Review focus:** Try the transfer form on both screen sizes, confirm the date and implied rate, then edit from either PiggyBank. The browser check also exposed and fixed profile loading for the README Bob account's `.test` email.

- [ ] Compact Type and Category selects
  - **Delivered:** The transaction form gives its Type and Category selects an intrinsic width with a two-rem arrow area, and keeps their labels above the controls on desktop and mobile.
  - **Evidence:** Frontend build and lint passed; Bob-only desktop/mobile form checks found no horizontal overflow and measured compact control widths of 223 and 251 pixels.
  - **Review focus:** Confirm the arrows sit near the selected text and long category labels remain readable.

- [ ] Shared themed dropdowns
  - **Delivered:** Added `ThemedSelect` with an in-app listbox, keyboard arrows, Enter, Escape, Home/End, type-ahead, touch-sized options, and a viewport-aware portal. Replaced every frontend `<select>` in Dashboard, Settings, PiggyBank forms and analytics, and Dashboard charts; option labels are plain text.
  - **Evidence:** Frontend build and lint passed. Bob-only desktop/mobile browser checks exercised keyboard and touch selection, viewport fit, Dashboard currency, and saving/restoring Settings transactions per page; no horizontal overflow was found.
  - **Review focus:** Check long category lists and all dropdown placements on desktop and mobile.

- [ ] Settings modal from every current page
  - **Delivered:** Dashboard and PiggyBank view open the same Profile, Display, Backup, and Danger Zone content in a modal; `/settings` opens it directly over Dashboard. Closing by Escape, backdrop, or close button returns focus to the opener and preserves page scroll. Display changes update the page underneath through the shared user context.
  - **Evidence:** Frontend build and lint passed. Desktop/mobile Bob browser checks covered focus cycling, Escape, direct link, viewport fit, and scroll restoration; changing the date format inside the modal immediately changed the PiggyBank list, then the original format was restored.
  - **Review focus:** Try Settings and each close method on desktop and mobile, including long modal scrolling.

- [ ] Scalable expense category charts
  - **Delivered:** Dashboard and PiggyBank analytics use one shared pie chart with a compact category-count control, scrollable sorted category panel, amounts, and percentages. Slice hover and click show category details. Rounded shares sum to exactly 100.0%.
  - **Evidence:** Frontend build and lint passed. Bob-only tests with 30 temporary categories showed both panels scroll without horizontal overflow; all temporary transactions were removed. The percentage helper summed to 100% for 2, 3, and 30-category fixtures. An isolated 390px layout check confirmed the panel stays inside the viewport.
  - **Review focus:** Inspect the slice tooltip and panel placement on desktop and mobile, including very long category names.

- [ ] PiggyBank transaction sorting and filtering
  - **Delivered:** The transaction list sorts by date or signed amount in either direction, filters by multiple categories and an optional typed date range, shows a matching count and empty state, and pages the filtered result. The date range also applies to PiggyBank analytics; PiggyBank transfers stay out of income and expense charts.
  - **Evidence:** Frontend build and lint passed. Four temporary Bob transactions confirmed category and date counts, amount sorting, and no mobile horizontal overflow; the test rows were deleted.
  - **Review focus:** Check the controls with a long ledger, including date-format changes and filtered pagination.

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
  - **Delivered:** Old card (lost): the 33 actual Transport rows from LudwigSingapore dated 2025-08-04 to 2025-08-23 (S$34.18) moved to EZLinkSG60, since they were paid by that card. Its funding is an initial balance from Yully (`transfer_in`, Allowance, S$16.79 on 2025-08-04, derived) plus the UOB top-ups of 2025-08-15 and 2025-08-22 (S$30). The S$5.29 lost with the card is now one EZLinkSG60 row (`Others`, 2025-08-24); the old `Ezlink Lost` PiggyBank transfer (#299 / #1162, whose EZLink side was dated 2025-10-17) was removed, so LudwigSingapore no longer carries that loss or those fares. Two `Trip (estimated)` rows (S$3.66 each, 2025-08-23/24) are needed for the recorded fares, top-ups, and S$5.29 loss to add up without a negative balance. To keep today's balance, the first 2026 estimate was dropped (2026-01-13) and the next reduced to S$2.91. The new card starts on 2025-08-25 with S$14.40. Estimated daily commute rows (`Commute: work/school`, `Trip: …`) from 2026-01-12 to 2026-11-04 were rebuilt from the owner's schedule so the balance stays between S$0 and S$40. Actual statement taps cover 2026-11-05 to 2026-11-18 (25 rows, bus fare refunds netted into each bus ride).
  - **Evidence:** Balance is S$12.62, matching the card on 2026-11-18; running balance stays between S$0.00 and S$38.97 from 2025-08-04 on; LudwigSingapore balance rose by S$39.47 (fares and the lost amount no longer charged to it); end of 2026-11-04 is S$22.12 as the statement implies. Backups are in `data/backups/`; row IDs to undo are in `data/ezlink-rebuild-*.json`, `data/ezlink-statement-*.json`, and `data/ezlink-oldcard-*.json`.
  - **Review focus:** The Yully initial balance and the two August trips are derived, and the January–October 2026 rows are estimates, not statement data. If the old card's real starting value is known, the two estimated trips can be adjusted to match.
