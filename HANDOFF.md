# Handoff

## Snapshot

- Updated: 2026-11-19. Branch: `main`.
- Open analytics filter menus now raise their containing glass panel above adjacent panels, fixing the Categories menu being covered by PiggyBank Analytics. Frontend build/lint passed; visual review remains in `REVIEW.md`.
- Combined Graph Analysis places PiggyBanks and Categories side by side with labels above the fields. Category filters in Graph Analysis and Reports now default to visibly checked options; All categories and Clear are distinct actions, with an empty-state prompt after Clear. Frontend build/lint passed; visual review is in `REVIEW.md`.
- Graph Analysis now removes Deposit/Withdrawal wording, filters chart data by category, and places a `Category Breakdown` control under the pie. The fixed pig FAB stays visible across protected dashboard, PiggyBank, analysis, and report pages, including open forms. Frontend build/lint passed; visual review is in `REVIEW.md`.
- Latest change: chart and report date labels now use the account's Settings date format, with numeric monthly labels. Monthly Summary groups using stored calendar dates. Deposit and Withdrawal were removed from the new transaction Type menu, while legacy entries retain their type when edited. Frontend build/lint passed; see `REVIEW.md` for visual checks.
- All agent-ready tasks from the current `TODO.md` have been implemented and moved to `REVIEW.md` for human review. The earlier implementation commits include `1f73547` and `4e797ce`.
- Latest desktop UI feedback fixed the PiggyBank Categories menu layout, replaced expanding Dashboard/Reports filter chips with searchable scrollable menus, themed the bulk actions, and widened the transaction Type control. These fixes are in `REVIEW.md`.
- PiggyBank Categories closes on outside click or Escape. Date fields now have an icon inside the input and an app-styled calendar while retaining typed entry. The calendar renders at the document root to avoid clipping, repositions above or below the field, and supports direct month/year selection. Graph Analysis and Reports open as separate pages from the larger fixed pig FAB, with back links to Dashboard or the PiggyBank. The FAB uses a line-art piggy-bank icon, centers its actions, expands on hover, and sits about 10px beyond the desktop content edge without covering transaction buttons. PiggyBank and combined balance charts now render smooth monotone curves through the same values. The PiggyBank analysis route passes its bank ID explicitly to prevent an endless Loading state. See `REVIEW.md`.
- The owner selected a fixed default of `1 SGD = 24.00 NTD`. New accounts receive it; the SQLAlchemy startup backfill adds it to existing accounts only when no SGD rate exists. Custom rates are preserved. The local Bob account shows the new default.
- The owner deferred mobile layout polish, automatic rate fetching, the finance chatbot, and monthly budgets/reminders. Those remain in `TODO.md`; monthly budget periods will run from the first through the last day of each month.
- Local `data/piggynest.db` and audit files are ignored by Git. No ledger row was changed by this final rate-default step.

## In-progress work

None. Await human review of `REVIEW.md`; begin the owner-led tasks when the owner reprioritizes them.

## Verification

- Backend: `cd backend && venv/bin/python -m pytest tests -q` — 52 passed, including new account defaults, rate validation and per-user isolation, and idempotent backfill that preserves custom rates.
- Frontend: `cd frontend && npm run build && npm run lint` — passed. Node 22 ledger and Reports calculation tests passed, including conversion through NTD, PiggyBank and bank transfers, empty calendar periods, and year boundaries.
- Isolated Playwright checks at 1280px and 390px covered page navigation, invalid jump input, live rate changes, net worth hiding after reload, Dashboard chips and charts, Reports figures and PiggyBank preselection, and horizontal overflow. Browser fixtures did not write database rows. The earlier 61-row Bob pagination check cleaned all temporary rows and restored Bob's 20-row page size.
- For the latest desktop UI fixes, a browser fixture with eight PiggyBanks and 30 categories verified menu search, scroll, fixed filter height, bulk actions, and matching Type/Date widths. Mobile design was not reviewed for these fixes, per the owner's current priority.
- An earlier isolated browser check verified category-menu closing and native date buttons. The subsequent custom-calendar and navigation changes passed frontend build/lint; Playwright was unavailable in the current Python environments and browser control was unavailable in this session, so these are awaiting visual review. The FAB now renders at the document root to avoid the page animation changing its fixed-position anchor.
