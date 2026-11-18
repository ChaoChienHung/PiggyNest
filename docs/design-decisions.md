# Design decisions and rationale

This page consolidates the former root and backend `DevNotes.md` files. It distinguishes implemented choices from older proposals.

## Database-centered application

The project began with a database-first approach because banks, transactions, and account ownership are central to its behavior. SQLAlchemy models describe storage, Pydantic schemas describe the API contract, and domain modules hold rules that can be reused without HTTP. A separate service layer was proposed for workflows spanning several repositories; the running API currently implements several of those workflows in route modules. Extract services when the same operation or invariant is duplicated, especially for transfer creation, deletion, and future editing.

The API is organized by resource under `app/api/v1/`, with route composition in `app/main.py`. This keeps related endpoints discoverable. An earlier proposal compared one large router (less boilerplate, harder to navigate), resource routers (clearer ownership, some repeated setup), and a hybrid with a version-level aggregator. The current structure uses resource routers; a dedicated aggregator is an optional later cleanup.

## Transfer integrity

Two signed rows preserve each bank's ledger while a shared UUID identifies one internal transfer. The two rows are committed or deleted together. An external transfer is a separate, single signed row with its own ID because the other account is outside the application. This distinction keeps external payments from being mistaken for broken internal transfers. Cross-currency internal transfers are rejected because the product has no exchange-rate model. Global spending excludes internal transfers. Legacy data is paired only when evidence is unique; ambiguous rows require a person to mark an external entry or confirm a pair.

## Visual design

The May 2026 visual refresh chose a pink and gold palette (`#ff8da1`, `#ffd166`) with cream backgrounds. `frontend/src/index.css` contains theme tokens, a drifting radial background, focus and button transitions, and lifted bank cards. The login and registration pages use a responsive split-screen layout, with an inline SVG pig and CSS-animated coins. Inline SVG avoids separate bitmap assets and stays sharp at different display sizes, at the cost of more JSX and CSS to maintain.

The pages use `.page-layout-container` and `.back-to-dashboard-link` for more spacious alignment. The pig-and-coin floating action menu uses a transparent `::before` pointer bridge so the hover menu stays reachable. The single-bank view includes a running-balance line chart, monthly cash-flow bar chart, and expense-category pie chart. Recharts renders interactive SVG elements; it handles chart layout and events, while CSS supplies the application theme. SVG sharpness is a useful reason for these charts, but smoothness depends on browser and chart size rather than being guaranteed by the format.

## Earlier proposals and current status

The old notes proposed FastAPI, login, piggy banks, currencies, aggregate costs, and replacing CSV storage; the running app implements these through the React/FastAPI/SQLite path. They also proposed storing only monthly summaries. Monthly summaries alone would discard the transaction detail needed for edits, audit, and backup, so any future materialized summary should be derived from the ledger. Streamlit was suggested as a test UI but is not part of the current application. See [backlog](backlog.md) for actionable remaining work.
