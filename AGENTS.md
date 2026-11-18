# PiggyNest agent rules

## Project boundary

- PiggyNest is a personal finance app with a FastAPI/SQLite API and a React/TypeScript frontend.
- Read the [README terminology](README.md#terminology) and [repository guide](README.md#repository-guide) before changing code or data. Use the feature links there to find the relevant documentation and folders.
- SQLAlchemy models define the persisted schema. The local development database is `data/piggynest.db`; tests use an isolated database. Do not change ledger rows by editing SQLite files directly.
- Keep the app usable with Python, pip, Node.js, and npm. The API and frontend have separate build and test commands.

## Non-regression rules

- Scope every bank, transaction, category, and backup operation to the authenticated user.
- A PiggyBank transfer creates two signed transactions atomically with one shared `transaction_id`; deleting either transaction or either PiggyBank removes both sides. Require matching currencies until conversion is implemented.
- A bank transfer (`transfer_out` or `transfer_in`) is one signed transaction with its own `entry:<id>` logical transaction ID. Do not infer that every unpaired historical transfer is broken; classify it with `backend/repair_transfer_ids.py` after review.
- Exclude PiggyBank transfers from income and spending totals. Keep bank transfer direction consistent with its signed amount.
- Keep the desktop and mobile transaction flows usable. Shared visual tokens live in `frontend/src/index.css`.

## Verification

- After backend changes, run `cd backend && venv/bin/python -m pytest tests -q`.
- After frontend changes, run `cd frontend && npm run build && npm run lint`.
- When transaction or backup behavior changes, cover both PiggyBank transfers and bank transfers with API tests. Review the affected form on desktop and mobile when its layout changes.

## Local manual testing

- Use the disposable Bob account described in the [README](README.md#development-test-account). Keep manual test data under Bob; never use its password for a deployed app.
