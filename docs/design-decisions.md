# Design decisions and rationale

This page consolidates the former root and backend `DevNotes.md` files. It distinguishes implemented choices from older proposals.

## Database-centered application

The project began with a database-first approach because banks, transactions, and account ownership are central to its behavior. SQLAlchemy models describe storage, Pydantic schemas describe the API contract, and domain modules hold rules that can be reused without HTTP. A separate service layer was proposed for workflows spanning several repositories; the running API currently implements several of those workflows in route modules. Extract services when the same operation or invariant is duplicated, especially for transfer creation, deletion, and future editing.

The API is organized by resource under `app/api/v1/`, with route composition in `app/main.py`. This keeps related endpoints discoverable. An earlier proposal compared one large router (less boilerplate, harder to navigate), resource routers (clearer ownership, some repeated setup), and a hybrid with a version-level aggregator. The current structure uses resource routers; a dedicated aggregator is an optional later cleanup.

## Transfer integrity

Two signed transactions preserve each PiggyBank's ledger while a shared UUID identifies one PiggyBank transfer. The two transactions are committed, edited, or deleted together. A bank transfer is a separate, single signed transaction with its own ID because the other account is outside the application. This distinction keeps payments to other people from being mistaken for broken PiggyBank transfers. Cross-currency PiggyBank transfers are rejected because the product has no exchange-rate model. Global spending excludes PiggyBank transfers. Legacy data is paired only when evidence is unique; ambiguous transactions require a person to mark a bank transfer or confirm a pair.

Monetary values use signed integer minor units in SQLite. This makes balances, paired transfer checks, and statistics exact at cent precision. The public API still uses ordinary major-unit numbers for compatibility. Inputs with more than two decimal places are rejected rather than silently rounded; the one-time old-database migration rounds existing Float values to cents. For the Ludwig CSV import, known sub-cent Float residue around whole NTD values is normalized explicitly before writing. A transfer with a source-side fee is represented as an equal-principal transfer pair plus a separate fee expense, preserving the original source-bank total.

## Multiple locations and account recovery

Two independent SQLite databases can assign the same numeric transaction ID to different records. The Excel importer remaps these IDs safely but cannot merge separate edits to the same PiggyBank. The chosen multi-location path is one shared backend with one persistent database, configured through the frontend and CLI API URLs. This avoids introducing a conflict algorithm into the backup format. Offline synchronization remains a separate proposal in [data synchronization](data-sync.md).

Email is the login identifier, while username is a display name. A reminder email helps users recover the latter; an eight-digit, short-lived code authorizes a password reset for a mailbox holder. The code is stored as a keyed digest, limited by time and attempts, and never returned by the API. Resetting the password increments the token version so old bearer tokens stop working. The flow and its remaining deployment requirements are in [account recovery](account-recovery.md).

## Visual design

The May 2026 visual refresh chose a pink and gold palette (`#ff8da1`, `#ffd166`) with cream backgrounds. `frontend/src/index.css` contains theme tokens, a drifting radial background, focus and button transitions, and lifted bank cards. The login and registration pages use a responsive split-screen layout, with an inline SVG pig and CSS-animated coins. Inline SVG avoids separate bitmap assets and stays sharp at different display sizes, at the cost of more JSX and CSS to maintain.

The pages use `.page-layout-container` and `.back-to-dashboard-link` for more spacious alignment. The pig-and-coin floating action menu uses a transparent `::before` pointer bridge so the hover menu stays reachable. The single-bank view includes a running-balance line chart, monthly cash-flow bar chart, and expense-category pie chart. Recharts renders interactive SVG elements; it handles chart layout and events, while CSS supplies the application theme. SVG sharpness is a useful reason for these charts, but smoothness depends on browser and chart size rather than being guaranteed by the format.

## Earlier proposals and current status

The old notes proposed FastAPI, login, piggy banks, currencies, aggregate costs, and replacing CSV storage; the running app implements these through the React/FastAPI/SQLite path. They also proposed storing only monthly summaries. Monthly summaries alone would discard the transaction detail needed for edits, audit, and backup, so any future materialized summary should be derived from the ledger. Streamlit was suggested as a test UI but is not part of the current application. See [backlog](backlog.md) for actionable remaining work.
