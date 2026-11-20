# Pending Cart, In-App Notifications, Recurring Schedules & Dark Mode

This document records the architecture, data-integrity invariants, and frontend engineering patterns behind four interconnected PiggyNest capabilities introduced in Alembic revision `0003_pending_notif_recurring`.

---

## 1. Pending Transactions ("Pending Cart")

### Problem & Motivation
Credit-card authorizations and online purchases often appear before the final settlement date (or final foreign-currency billed amount) is known. Recording them immediately in `transactions` would distort current balances, reports, and balance curves before money actually settles.

### Design: Dedicated Staging Table vs. Status Column
PiggyNest stores unconfirmed entries in a dedicated `pending_transactions` table (`backend/app/models/pending_transaction.py`) rather than adding a `status` flag to `transactions`:

- **Zero leakage into ledger invariants:** Every balance calculation, chart aggregation, numeric report, transfer-pair validator, and Excel backup query reads `transactions` and remains 100% unaffected by unconfirmed items.
- **Undecided dates:** `expected_date` is nullable (`YYYY-MM-DD` string), allowing users to stage charges before a settlement date exists.
- **Exact minor-unit storage:** Just like `transactions`, amounts use `amount_minor: BigInteger` via `to_minor_units` / `from_minor_units` to avoid IEEE-754 floating-point drift.

### Atomic Confirmation State Machine
`POST /api/v1/pending-transactions/{id}/confirm` executes inside a single SQLAlchemy transaction:
1. Validates user ownership and confirms `status == "pending"` (prevents double-confirmation with HTTP 400).
2. Allows final overrides for `date`, `amount`, `category`, `description`, and `piggy_bank_id` (defaulting `date` to `expected_date` or today).
3. Inserts the real `Transaction` row, flushes to obtain its `id`, sets `status = "confirmed"`, links `confirmed_transaction_id`, records `confirmed_at`, and writes an idempotent in-app `Notification` (`event_key = "pending_confirmed:{pending_id}"`).
4. Commits atomically — if any step fails, nothing is partially written.

---

## 2. In-App Notification Center (with Popup Letter Modal)

### Architecture & Idempotency
The `notifications` table (`backend/app/models/notification.py`) serves as the user's in-app inbox and is designed to share event semantics with future SMTP email alerts (e.g., monthly budget threshold notifications).

- **Stateful deduplication (`event_key`):** A composite unique constraint `UNIQUE(user_id, event_key)` guarantees that automated producers (recurring schedule runners, pending confirmation hooks, or future budget alerts) can call `create_notification(..., event_key=...)` safely across backend restarts or repeated API calls without ever creating duplicate letters.
- **Per-user scoping:** Every endpoint (`GET /api/v1/notifications`, `PUT /{id}/read`, `POST /read-all`, `DELETE /{id}`) filters strictly by `current_user.id`.
- **Frontend Letter UX:** `NotificationCenterModal` displays unread count badges and a scannable inbox; clicking any item marks it read and opens a formatted popup letter view (`notification-letter-paper`) with kind tag, user-formatted date, multi-line body, and Back/Delete actions.

---

## 3. Recurring Transactions (Stateful & Idempotent)

### Data Model
Two tables work together (`backend/app/models/recurring_rule.py`):
- **`recurring_rules`:** Stores the schedule template (`piggy_bank_id`, `amount_minor`, `type`, `category`, `description`), cadence (`frequency` in `daily | weekly | monthly | yearly`, `interval >= 1`), calendar-date bounds (`start_date`, `next_run_date`, optional `end_date`), and lifecycle `status` (`active | paused | stopped`).
- **`recurring_executions`:** An append-only idempotency ledger with `UNIQUE(rule_id, scheduled_date)`. Even if the server restarts mid-run or `run-due` is invoked multiple times, SQLite enforces at the schema level that a scheduled date can never be posted twice.
- **`transactions.recurring_rule_id`:** Nullable foreign key (`ON DELETE SET NULL`) linking generated transactions back to their rule so editing a transaction lets the user pause or stop future runs without deleting historical entries.

### Calendar-Date Arithmetic (No Timezone / DST Drift)
All schedule dates are stored as ISO `YYYY-MM-DD` strings rather than UTC timestamps (`backend/app/domain/recurring.py`):
- **`advance_date(current, frequency, interval, anchor_day)`** advances purely in calendar space.
- **Month-end clamping with anchor preservation:** A monthly schedule anchored on the 31st advances `2026-01-31 → 2026-02-28 → 2026-03-31` (clamping February to 28/29 while remembering `anchor_day = 31` for March). Yearly schedules handle leap-day `Feb 29 → Feb 28` cleanly.

### Pause, Stop & Delete Semantics
- **Pause (`status = "paused"`):** Skips future due runs while retaining `next_run_date`; can be resumed later.
- **Stop (`status = "stopped"`):** Permanently halts future runs (also set automatically when `next_run_date > end_date`).
- **Delete (`DELETE /api/v1/recurring/{id}`):** Clears `transactions.recurring_rule_id` explicitly before deleting the rule so all historical ledger entries remain intact.
- **Initial-entry attachment:** When a user creates a transaction with "Repeat automatically" enabled, the frontend passes `initial_transaction_id` to `POST /api/v1/recurring`, recording `start_date` in `recurring_executions` and advancing `next_run_date` by one interval so the first occurrence is never double-posted.

---

## 4. Dark Mode (Soft Dark-Plum Theme)

### Token Architecture
PiggyNest uses semantic CSS custom properties in `frontend/src/index.css`:
- `:root` defines the default Light (Soft Pastel) palette.
- `[data-theme="dark"]` overrides the same variables with a **Soft Dark-Plum** palette (`#1a131d` / `#251b2a` / `#312437` backgrounds, `#f5edf7` / `#cbb8d0` text, `#ff8da1` coral-pink accent, `#ffd166` gold coin) derived directly from the dark-plum favicon (`frontend/public/piggynest.svg`).
- Chart tokens (`--chart-tooltip-bg`, `--chart-grid`, `--chart-axis`, `--chart-area-fill`) ensure Recharts tooltips and grids adapt automatically without hardcoded white backgrounds.

### Zero-Flash Persistence (FOUC Prevention)
- `ThemeProvider` (`frontend/src/context/ThemeContext.tsx`) persists the user's choice under `localStorage['piggynest-theme']` and updates `document.documentElement[data-theme]` plus `<meta name="theme-color">`.
- A tiny synchronous inline `<script>` in `frontend/index.html` reads `localStorage['piggynest-theme']` before React mounts, eliminating any light-mode flash on page reload.
- Users can toggle themes from the header (`HeaderQuickTools`), the Login screen, or `Settings → Display → Appearance`.

---

## 5. Schema Migration Safety (`0003_pending_notif_recurring`)

- **Alembic batch mode:** `render_as_batch=True` allows SQLite to add `transactions.recurring_rule_id` with an index and foreign key cleanly, and `downgrade()` reverses all four tables and the column cleanly.
- **Pre-Alembic database bridging (`backend/app/db/migrations.py`):** `_bring_pre_alembic_db_to_baseline` restricts `Base.metadata.create_all` to the six `0001_initial_schema` baseline tables (`BASELINE_TABLES`), ensuring legacy pre-Alembic databases stamp cleanly at `0001` and then advance sequentially through `0002` and `0003` without table-already-exists collisions.
