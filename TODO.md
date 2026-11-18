# TODO

## Task rules

- Write one task per checkbox with a clear outcome and acceptance criteria.
- Record scope and dependencies only when they affect implementation.
- Keep long-term ideas here until they are accepted, rejected, or completed. Completed work awaiting human review belongs in [REVIEW.md](REVIEW.md); the current stopping point belongs in [HANDOFF.md](HANDOFF.md).

## Agent-ready

No outstanding tasks.

## Later

- [ ] Polish the mobile layout after the desktop flows are settled.
  - **Priority:** Deferred by the owner. Focus current UI work on desktop.
  - **Scope:** Review Dashboard, PiggyBank transactions and forms, charts, Reports filters, and Settings at common phone widths; keep controls readable and reachable without horizontal overflow.
  - **Acceptance:** The main add, edit, transfer, filter, report, and settings flows work by touch on a narrow screen, with no clipped content or controls covering one another.

## Owner-led

- [ ] Fetch exchange rates automatically from a free rate API.
  - **Priority:** Deferred by the owner until the basic features are settled.
  - **Context:** Currency conversion starts with fixed rates entered in Settings.
  - **Decision needed:** Choose the rate provider, refresh frequency, and whether an automatic rate replaces the user's fixed rate or is offered as a suggestion.
  - **Acceptance:** Rates refresh on the agreed schedule with their source and date shown; if the provider is unavailable, the last known or fixed rate is used and labeled as such.

- [ ] Add a finance-planning chatbot.
  - **Priority:** Deferred by the owner until the basic features are settled.
  - **Decision needed:** Choose an AI provider, data-sharing boundary, and whether advice can use individual transactions.
  - **Acceptance:** Users can ask about spending and savings plans from the app; private ledger data is sent only under the agreed policy.

- [ ] Add monthly budget planning and reminders.
  - **Priority:** Deferred by the owner until later.
  - **Decision:** Budget periods run from the first through the last day of each month. The owner is open to app and email reminders; settle delivery and essential-spending rules when implementation starts.
  - **Acceptance:** Users can set a monthly plan and see remaining spend, overspending, and the agreed start-of-month reminder.
