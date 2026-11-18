# PiggyNest agent rules

## Project boundary

- PiggyNest is a personal finance app with a FastAPI/SQLite API and a React/TypeScript frontend.
- SQLAlchemy models in `backend/app/models/` define the persisted schema. The local development database is `backend/data/piggynest.db` when the API starts from `backend/`; tests use an isolated database. Do not change ledger rows by editing SQLite files directly.
- Keep the app usable with Python, pip, Node.js, and npm. The API and frontend have separate build and test commands.

## Non-regression rules

- Scope every bank, transaction, category, and backup operation to the authenticated user.
- An internal transfer between two PiggyBanks creates two signed rows atomically with one shared `transaction_id`; deleting either row or either bank removes both sides. Require matching currencies until conversion is implemented.
- An external `transfer_out` or `transfer_in` is one signed row with its own `entry:<id>` transaction ID. Do not infer that every unpaired historical transfer is broken; classify it with `backend/repair_transfer_ids.py` after review.
- Exclude internal transfers from income and spending totals. Keep external transfer direction consistent with its signed amount.
- Keep the desktop and mobile transaction flows usable. Shared visual tokens live in `frontend/src/index.css`.

## Verification

- After backend changes, run `cd backend && venv/bin/python -m pytest tests -q`.
- After frontend changes, run `cd frontend && npm run build && npm run lint`.
- When transaction or backup behavior changes, cover both internal and external transfers with API tests. Review the affected form on desktop and mobile when its layout changes.

## Local manual test account

- Use Bob in the local `backend/data/piggynest.db`: username `Bob`, login `bob@piggynest.test`, password `BobTest2026!`. If the database is new, register Bob through the app first.
- This is a disposable local account. Keep manual test data under Bob; never use this password for a deployed app.

## Where to look

- Setup and everyday commands: `README.md`
- Architecture and transaction contracts: `docs/architecture.md`
- Design decisions and stack: `docs/design-decisions.md`, `docs/tech-stack.md`
- Historical transfer repair: `docs/transfer-repair.md`
- Current work: `TODO.md`, `docs/backlog.md`
