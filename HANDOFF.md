# Handoff

## Snapshot

- Updated: 2026-11-19. Branch: `main`.
- Last pushed commit: `1f73547` completed the first seven TODO items and the Ludwig description cleanup, including `Qashier-MUYOO` → `Bread` and `Qashier-AGZ Food` → `Lunch`/`Dinner` by the owner's same-day rule. See `REVIEW.md` for evidence and review points.
- Current implementation adds scalable category charts, PiggyBank transaction sorting/filtering and direct page navigation, fixed-rate conversion, a combined net-worth card, combined Dashboard analytics, and a Reports view. The first three are in `REVIEW.md`; the currency and report work remains in `TODO.md` until its default rate is chosen and applied.
- The local development database `data/piggynest.db` is ignored by Git. Ledger rows were never edited through SQLite files. A 61-row Bob pagination check cleaned all temporary transactions and restored Bob's 20-row page size. The later browser checks used isolated fixtures without database writes.

## In-progress work

- Awaiting the owner's SGD → NTD default rate for new users. The rate table, validation, Settings UI, conversion helper, net worth, Dashboard charts, and Reports are implemented. Add the chosen default to account registration and safely backfill existing accounts that have no SGD rate. Do not overwrite a user's saved rate.
- The owner's decisions are also pending for the `Owner-led` tasks in `TODO.md`: automatic-rate provider/schedule/replacement policy, chatbot provider/data boundary, and budget periods/reminders.
- After the default rate is set, verify the full backend suite and frontend build/lint, check the browser at desktop and mobile widths, then move the remaining completed `Agent-ready` items from `TODO.md` to `REVIEW.md` and commit/push. Keep owner-led items in TODO until their decisions and implementation are complete.

## Verification so far

- Backend suite: 51 passed before the latest rate-currency validation adjustment; rerun required after final rate default changes.
- Frontend build/lint passed after the restored money-flow pie.
- `frontend/tests/ledgerAnalytics.test.mjs` and `reportMath.test.mjs` pass under Node 22 with `--experimental-strip-types` (currency conversion, transfer treatment, empty calendar periods, year boundary).
- Isolated Playwright checks at 1280px and 390px verified page links and invalid page entry, live rate edits, net worth hiding after reload, Dashboard bank chips and metric switching, Reports figures, the prefiltered PiggyBank Reports link, and no horizontal overflow, including after the money-flow pie was restored.
