# Engineering Optimizations

This document records the background, rationale, implementation details, and measured impact of PiggyNest's core engineering foundation upgrades.

---

## 1. Alembic Versioned Database Migrations

### Background
Previously, `backend/app/main.py` initialized the SQLite database at import time using `Base.metadata.create_all(bind=engine)` followed by a growing chain of hand-written `inspect(...)` + `ALTER TABLE ... ADD COLUMN` blocks and separate one-off scripts (`migrate_db.py`, `migrate_db_v3.py`).

### Why
- Inline `ALTER TABLE` blocks do not record schema history, cannot be rolled back (`downgrade`), and become fragile as upcoming features (such as recurring transactions and monthly budget/notification tables) introduce multi-column changes, foreign keys, and indexes.
- `Base.metadata.create_all` never updates existing tables, creating a split between fresh installs and upgraded databases.
- SQLite requires table-recreation ("batch mode") for many `ALTER TABLE` operations; Alembic handles this safely via `render_as_batch=True`.

### What Changed
- Added `alembic>=1.13.0,<2.0.0` to `backend/requirements.txt` and configured `backend/alembic.ini` and `backend/migrations/env.py` (with `render_as_batch=True`; named `migrations/` rather than `alembic/` so it never shadows the `alembic` package in editors or type checkers).
- Imported `Category` in `backend/app/db/base.py` so `Base.metadata` includes all six SQLAlchemy models.
- Created the baseline revision `backend/migrations/versions/0001_initial_schema.py` matching the current production schema (with full `upgrade()` and `downgrade()` support).
- Added `backend/app/db/migrations.py` (`run_migrations(engine)`), called on API startup in `backend/app/main.py`:
  - **Fresh databases:** run `alembic upgrade head` from scratch.
  - **Existing pre-Alembic SQLite databases** (such as a developer's existing `data/piggynest.db` that has `users` without `alembic_version`): bring any missing pre-baseline columns/tables up to the baseline (`migrate_money` + legacy column checks) without touching ledger rows, stamp `0001_initial_schema`, and then run `alembic upgrade head`.
  - **Already-versioned databases:** apply only pending revisions up to `head`.
- Removed obsolete one-off scripts `backend/migrate_db.py` and `backend/migrate_db_v3.py`.

### Benefits, Impact & Measured Results
- **Safe future schema evolution:** New features can generate deterministic revisions with `cd backend && venv/bin/python -m alembic revision --autogenerate -m "..."` and apply them via `venv/bin/python -m alembic upgrade head` (or automatically on startup).
- **Zero-downtime transition for existing users:** Verified by `backend/tests/test_migrations.py` across three scenarios: fresh DB creation + idempotency, bridging a legacy pre-Alembic DB with float `amount` without losing rows, and full `downgrade base` → `upgrade head` round-trip.
- **Cleaner startup:** Replaced 24 lines of ad-hoc DDL in `backend/app/main.py` with a single `run_migrations(engine)` call.

---

## 2. Configuration Consolidation & Legacy Module Cleanup

### Background
Early versions of PiggyNest stored records in local CSV/JSON files and synced via Google Drive. Over time, the app moved to FastAPI + SQLite, leaving behind:
- `backend/app/core/config.py` importing `yaml` (not listed in `backend/requirements.txt`) and attempting to read `./config/config.yaml`, while the shipped file actually lived at `backend/app/core/config.yaml` and contained obsolete `./src/accounts.json` paths and a hardcoded Google Drive `folder_id`.
- Four unimported legacy domain modules (`backend/app/domain/account.py`, `categories.py`, `reports.py`, `transactions.py`) that depended on `pandas` (also not in `requirements.txt`) or broken imports.
- An empty 0-byte `requirements.txt` at the repository root.

### Why
- Dead configuration paths and hidden dependencies (`yaml`, `pandas`) mislead developers and break fresh environments if accidentally imported.
- Removing hardcoded external IDs (`folder_id`) and unifying configuration around environment variables + `backend/.env` establishes a single source of truth for local and deployed backends.

### What Changed
- Simplified `backend/app/core/config.py` to use Pydantic v2 `SettingsConfigDict` loading exclusively from environment variables and `backend/.env` (resolved relative to `backend/` regardless of working directory).
- Updated `backend/.env.example` to document `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_ORIGINS`, and SMTP settings.
- Removed `backend/app/core/config.yaml`, the four unused legacy domain modules, and the empty root `requirements.txt`.

### Benefits, Impact & Measured Results
- **Single source of truth:** Every backend setting is now configurable via environment variables or `backend/.env` with zero YAML path mismatch.
- **No phantom dependencies:** `backend/app/` no longer imports unlisted packages (`yaml`, `pandas`), making fresh `venv` setup reliable from `backend/requirements.txt` alone.
- **Zero regression:** All 72 backend tests pass after removal.

---

## 3. Frontend Route-Based Code Splitting

### Background
`frontend/src/App.tsx` statically imported every route (`Login`, `Register`, `AccountRecovery`, `Dashboard`, `PiggyBankView`, `Reports`, `Analysis`, `SettingsDialog`). Vite therefore bundled the entire application—including the charting stack (`recharts`)—into a single monolithic JavaScript file.

### Why
- Users opening `/login` or `/` (Dashboard) were forced to download and parse the entire charting library and every secondary page before first paint.
- Vite emitted a production build warning (`Some chunks are larger than 500 kB after minification`).

### What Changed
- Converted all route-level page components and `SettingsDialog` in `frontend/src/App.tsx` to `React.lazy(...)` dynamic imports wrapped in a shared `<Suspense fallback={<RouteFallback />}>`.

### Benefits, Impact & Measured Results
Measured with `cd frontend && npm run build`:

| Metric | Before (Monolithic) | After (Route-Split) | Change |
| --- | ---: | ---: | ---: |
| Initial entry JS (`index-*.js`) | `756.20 kB` | `275.87 kB` | **-63.5%** |
| Initial entry JS (gzip) | `231.04 kB` | `91.10 kB` | **-60.6%** |
| Vite `> 500 kB` chunk warning | Triggered | **Eliminated** | Resolved |
| `Login` route chunk | Bundled in entry | `3.23 kB` (`1.34 kB` gzip) | On-demand |
| `Dashboard` route chunk | Bundled in entry | `9.64 kB` (`3.60 kB` gzip) | On-demand |
| `Reports` route chunk | Bundled in entry | `6.12 kB` (`2.51 kB` gzip) | On-demand |
| `Analysis` route chunk | Bundled in entry | `6.55 kB` (`2.48 kB` gzip) | On-demand |

- **Faster initial load:** Login, Dashboard, and Reports pages no longer download or parse the charting-heavy chunk (`PiggyBankView-*.js`, `414.92 kB` / `122.10 kB` gzip) until needed.
- **Better browser caching:** Updating one page only invalidates that route's small chunk instead of forcing clients to re-download the entire app bundle.

---

## 4. Python Bytecode Tracking Cleanup

### Background
`.gitignore` did not exclude `__pycache__/` or `*.py[cod]`, so 23 `.cpython-312.pyc` files were tracked in Git and running Python 3.15 locally left untracked `.cpython-315.pyc` files showing up as dirty changes in `backend/`.

### Why
- Compiled bytecode is machine- and Python-version-specific, pollutes diffs, and can cause confusing `git status` noise or accidental commits.

### What Changed
- Added `__pycache__/`, `*.py[cod]`, and `*$py.class` to `.gitignore`.
- Untracked all 23 cached `.pyc` files from `HEAD` (`git rm --cached`) and deleted the stale `.cpython-315.pyc` files.

### Benefits, Impact & Measured Results
- Clean `git status` across Python versions; future bytecode caches are ignored automatically.
