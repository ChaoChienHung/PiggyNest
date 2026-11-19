# TODO

## Task rules

- Write one task per checkbox with a clear outcome and acceptance criteria.
- Record scope and dependencies only when they affect implementation.
- Keep long-term ideas here until they are accepted, rejected, or completed. Completed work awaiting human review belongs in [REVIEW.md](REVIEW.md); the current stopping point belongs in [HANDOFF.md](HANDOFF.md).

## Agent-ready

- [ ] Add recurring transactions (auto-scheduled entries with stop/pause on edit).
  - **Scope:** Allow attaching a recurrence rule (interval such as weekly/monthly/yearly or custom cadence, optional end date) when creating a transaction; editing that transaction/rule allows pausing or stopping future occurrences without deleting past transactions. Store stateful run metadata (`next_run_date` / executed periods) in SQLite so backend restarts or repeated triggers never double-post.
  - **Acceptance:** Due occurrences post atomically and idempotently; stopping/pausing a rule halts future runs while keeping historical entries intact; covered by backend tests and desktop UI flows.

## Owner-led

- [ ] Add monthly savings & budget planning with stateful email notifications.
  - **Priority:** Owner wants to design the detailed planning and notification rules before implementation.
  - **Context & Design Direction:**
    - Budget periods run from the first through the last day of each month.
    - Users create a monthly savings & spending plan based on monthly income (auto-sum actual monthly income excluding PiggyBank transfers, or manual expected income), set a savings target, and allocate spending limits across categories with in-app progress bars.
    - Notifications must be **stateful** with a persisted per-period/threshold counter in the database so backend restarts never re-send duplicate emails.
    - Alert thresholds should be user-configurable (e.g., approaching at 70% / 80%, reaching 100%, significantly exceeding 120%+) rather than hardcoded to a single count.
  - **Decision needed:** Finalize the exact planning UX, essential-spending vs discretionary rules, configurable alert threshold structure, and notification cadence/limits.
  - **Acceptance:** Users can configure a monthly savings & spending plan, view live progress bars for remaining spend and overspending, and receive stateful email/app notifications according to their configured thresholds without duplicate sends across restarts.

- [ ] Polish the mobile layout after the desktop flows are settled.
  - **Priority:** Deferred by the owner. Focus current UI work on desktop.
  - **Scope:** Review Dashboard, PiggyBank transactions and forms, charts, Reports filters, and Settings at common phone widths; keep controls readable and reachable without horizontal overflow.
  - **Acceptance:** The main add, edit, transfer, filter, report, and settings flows work by touch on a narrow screen, with no clipped content or controls covering one another.

- [ ] Fetch exchange rates automatically from a free rate API.
  - **Priority:** Deferred by the owner until the basic features are settled.
  - **Context:** Currency conversion starts with fixed rates entered in Settings.
  - **Decision needed:** Choose the rate provider, refresh frequency, and whether an automatic rate replaces the user's fixed rate or is offered as a suggestion.
  - **Acceptance:** Rates refresh on the agreed schedule with their source and date shown; if the provider is unavailable, the last known or fixed rate is used and labeled as such.

- [ ] Add a finance-planning chatbot.
  - **Priority:** Deferred by the owner until the basic features are settled.
  - **Decision needed:** Choose an AI provider, data-sharing boundary, and whether advice can use individual transactions.
  - **Acceptance:** Users can ask about spending and savings plans from the app; private ledger data is sent only under the agreed policy.
