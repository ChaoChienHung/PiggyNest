# TODO

## Task rules

- Write one task per checkbox with a clear outcome and acceptance criteria.
- Record scope and dependencies only when they affect implementation.
- Keep long-term ideas here until they are accepted, rejected, or completed. Completed work awaiting human review belongs in [REVIEW.md](REVIEW.md); the current stopping point belongs in [HANDOFF.md](HANDOFF.md).

## Agent-ready

- [ ] Replace the default website icon with a PiggyNest icon.
  - **Context:** The frontend still ships the Vite starter icon.
  - **Scope:** Browser favicon and related page metadata in `frontend/`; use one recognizable pig or PiggyBank design that fits the existing theme.
  - **Acceptance:** The PiggyNest icon appears in the browser tab at common sizes, with no Vite branding left in shipped assets.

- [ ] Move the pig's Additional Tools menu into a floating action button (FAB).
  - **Scope:** Dashboard and PiggyBank view; move the analytics toggle from the inline pig menu into the FAB's revealed actions.
  - **Acceptance:** The FAB stays clear of primary buttons and content, reveals Graph Analysis on hover and keyboard focus, and can be opened and used by touch on mobile.

- [ ] Consolidate duplicate withdrawal and miscellaneous categories.
  - **Decision:** Use `Withdrawals` as the category label (a noun, unlike `Withdraw`) and `Other` as the fallback category label.
  - **Scope:** Existing user categories and transaction references, defaults, import behavior, and category controls. Keep the `withdrawal` transaction type distinct from its category.
  - **Acceptance:** `Withdraw`, `Withdrawal`, and `Withdrawals` resolve to one `Withdrawals` category; `Others` and `Other` resolve to one `Other` category per user. Existing amounts, balances, and transfer links remain unchanged, including after repeated migration or import.

- [ ] Add a category for functional software and digital services.
  - **Decision:** Use `Software & Digital Services` for Claude, Gemini Pro, and similar work or productivity tools. A recurring payment remains a subscription in its description; `Entertainment` remains for leisure.
  - **Scope:** Category defaults and classification guidance; review existing AI-tool transactions before reclassifying them.
  - **Acceptance:** New users can select the category, existing users can add it without duplicates, and known Claude/Gemini Pro expenses are classified consistently without changing their amounts or dates.

- [ ] Bring the Type and Category select arrows closer to their labels in transaction forms.
  - **Scope:** Shared form styles on desktop and mobile.
  - **Acceptance:** Both controls remain legible and their arrow placement is visually consistent at narrow and wide widths.

## Owner-led

- [ ] Show the three largest currency balances and one converted total balance on the dashboard.
  - **Decision needed:** Choose a base currency and exchange-rate source/refresh policy. Label the converted sum as a balance or net worth, not revenue.
  - **Acceptance:** The dashboard shows the top three currencies, a converted total with its base currency and rate timestamp, and a clear unavailable-rate state.

- [ ] Add a finance-planning chatbot.
  - **Decision needed:** Choose an AI provider, data-sharing boundary, and whether advice can use individual transactions.
  - **Acceptance:** Users can ask about spending and savings plans from the app; private ledger data is sent only under the agreed policy.

- [ ] Add monthly budget planning and reminders.
  - **Decision needed:** Define budget periods, essential-spending rules, and reminder delivery.
  - **Acceptance:** Users can set a monthly plan and see remaining spend, overspending, and the agreed start-of-month reminder.
