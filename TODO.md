# TODO

## Task rules

- Write one task per checkbox with a clear outcome and acceptance criteria.
- Record scope and dependencies only when they affect implementation.
- Keep long-term ideas here until they are accepted, rejected, or completed. Completed work awaiting human review belongs in [REVIEW.md](REVIEW.md); the current stopping point belongs in [HANDOFF.md](HANDOFF.md).

## Agent-ready

- [ ] Convert balances between currencies for display, using fixed rates the user sets.
  - **Progress:** Per-user rates, validation, Settings editing, conversion, net worth, analytics, and Reports are implemented. Waiting for the owner's default SGD → NTD rate before seeding new and existing accounts without a saved SGD rate.
  - **Decision:** For now, use fixed exchange rates instead of a rate API. Each user sets them in Settings in one format: one row per currency they hold other than the display currency, read as `1 SGD = [ 23.50 ] NTD` with a number field (positive, up to 4 decimal places). New users start from a built-in default rate that the owner provides when this is implemented, so totals work before the user edits anything. The default display currency is NTD and can be switched. Conversion is for display only and never changes stored amounts.
  - **Scope:** Per-user rate table and display currency on the backend (alongside date format), validated and saved through the user settings API; a Settings section to view and edit rates, showing when each was last changed; one shared frontend helper for converted amounts, which converts through NTD when neither currency is NTD. Required by the net worth card and Dashboard analytics below.
  - **Acceptance:** Any balance can be shown in NTD or SGD; hovering a converted amount shows the rate used and when it was set; editing a rate updates every converted total immediately; a currency with no rate shows a clear "rate needed" prompt linking to Settings instead of a wrong total. Backend tests cover per-user rates and validation.

- [ ] Redesign the Total Net Worth card as one combined total.
  - **Context:** The card currently lists each currency as its own total, and earlier versions showed a single line such as `Total Net Worth   748,677.00`.
  - **Depends on:** Fixed-rate currency conversion.
  - **Scope:**
    - One headline total: every PiggyBank converted to the selected display currency and summed.
    - A themed currency dropdown beside the total (default NTD).
    - An eye button that hides every amount on the card as `****` and shows it again on the next press; remember the choice per user.
    - Below the total, the top five currencies by converted value, each with its original-currency amount (for example, NT$ 520,000.00 and S$ 9,800.00) and its share of the total.
  - **Acceptance:** The total equals the sum of converted PiggyBank balances; switching currency updates the total and keeps the per-currency rows in their own currency; hidden mode masks every amount on the card, including after reload; the layout works on desktop and mobile.

- [ ] Make Dashboard analytics combine selected PiggyBanks in one currency.
  - **Context:** Dashboard analytics currently shows NTD and SGD as separate series; they should be one combined total converted to the display currency.
  - **Depends on:** Fixed-rate currency conversion.
  - **Scope:** By default every PiggyBank is included and converted to the display currency (default NTD) before summing. A tag-style selector lists each PiggyBank as a chip; unchecking a chip removes it from every chart, with "Select all" and "Clear all" actions. Add the same date range control as the PiggyBank view. PiggyBank transfers between selected banks stay excluded from income and spending.
  - **Acceptance:** With all PiggyBanks selected, the balance series ends at the net worth total; unchecking a PiggyBank removes it from every Dashboard chart; Clear all shows an empty-state prompt; the selection and date range survive switching chart metrics; works on desktop and mobile.

- [ ] Add a Reports view with numeric summaries.
  - **Context:** Analytics shows charts; Reports shows the numbers behind them.
  - **Scope:** A Reports page reachable from the Dashboard (and the PiggyBank view, pre-filtered to that PiggyBank). For income, spending, and net change, show total, average, minimum, and maximum per day, per month, and per year, plus the number of transactions; name the day, month, or year where each minimum and maximum occurred. Use the same filters as Dashboard analytics: PiggyBank tags (default all), categories, date range, and display currency (amounts converted with the fixed rates). PiggyBank transfers stay excluded from income and spending. Periods with no transactions count as zero for averages; state this on the page.
  - **Depends on:** Fixed-rate currency conversion and the PiggyBank tag selector from Dashboard analytics; reuse their components.
  - **Acceptance:** Numbers match a hand calculation on a small fixture for each period; changing any filter updates every figure; values respect the user's date format and the net-worth hide setting; layout works on desktop and mobile. Backend or frontend tests cover the aggregation, including month and year boundaries and transfers.

## Owner-led

- [ ] Fetch exchange rates automatically from a free rate API.
  - **Context:** Currency conversion starts with fixed rates entered in Settings.
  - **Decision needed:** Choose the rate provider, refresh frequency, and whether an automatic rate replaces the user's fixed rate or is offered as a suggestion.
  - **Acceptance:** Rates refresh on the agreed schedule with their source and date shown; if the provider is unavailable, the last known or fixed rate is used and labeled as such.

- [ ] Add a finance-planning chatbot.
  - **Decision needed:** Choose an AI provider, data-sharing boundary, and whether advice can use individual transactions.
  - **Acceptance:** Users can ask about spending and savings plans from the app; private ledger data is sent only under the agreed policy.

- [ ] Add monthly budget planning and reminders.
  - **Decision needed:** Define budget periods, essential-spending rules, and reminder delivery.
  - **Acceptance:** Users can set a monthly plan and see remaining spend, overspending, and the agreed start-of-month reminder.
