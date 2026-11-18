# Handoff

## Snapshot

- Updated: 2026-11-19. Branch: `main`.
- All agent-ready tasks from the current `TODO.md` have been implemented and moved to `REVIEW.md` for human review. The earlier implementation commits include `1f73547` and `4e797ce`.
- Latest desktop UI feedback fixed the PiggyBank Categories menu layout, replaced expanding Dashboard/Reports filter chips with searchable scrollable menus, themed the bulk actions, and widened the transaction Type control. These fixes are in `REVIEW.md`.
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
