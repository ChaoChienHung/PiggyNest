# TODO

## Task rules

- Write one task per checkbox with a clear outcome and acceptance criteria.
- Record scope and dependencies only when they affect implementation.
- Keep long-term ideas here until they are accepted, rejected, or completed. Completed work awaiting human review belongs in [REVIEW.md](REVIEW.md); the current stopping point belongs in [HANDOFF.md](HANDOFF.md).

## Agent-ready

- [ ] Replace empty transaction descriptions with meaningful text.
  - **Context:** Some descriptions are SQL `NULL`, blank, or the literal string `Null`; for example, an Interest transaction should say `Interest`.
  - **Scope:** Audit all users' transactions by ID, infer a description from the transaction category, type, transfer counterparty, or verified source record, and update through SQLAlchemy. Record any cases where those facts do not support a specific description before choosing a generic type-based label.
  - **Acceptance:** No transaction retains a null-like description; Interest entries read `Interest`; every changed ID has an auditable before/after record; amounts, dates, categories, balances, and transfer links are unchanged. Re-running the cleanup makes no further changes.

- [ ] Replace the default website icon with a PiggyNest icon.
  - **Context:** The frontend still ships the Vite starter icon.
  - **Scope:** Browser favicon and related page metadata in `frontend/`; use one recognizable pig or PiggyBank design that fits the existing theme.
  - **Acceptance:** The PiggyNest icon appears in the browser tab at common sizes, with no Vite branding left in shipped assets.

- [ ] Move the pig's Additional Tools menu into a floating action button (FAB).
  - **Scope:** Dashboard and PiggyBank view; move the analytics toggle from the inline pig menu into the FAB's revealed actions.
  - **Acceptance:** The FAB stays clear of primary buttons and content, reveals Graph Analysis on hover and keyboard focus, and can be opened and used by touch on mobile.

- [ ] Support PiggyBank transfers between different currencies, with a transfer date.
  - **Context:** `POST /api/v1/transfers` rejects SGD ↔ NTD transfers ("Transfers require matching currencies"), so a transfer such as UnitedOverseasBank → LudwigTaiwan cannot be recorded as one linked transfer. The transfer form also has no date field and always records the current time.
  - **Decision:** Do not fetch exchange rates. For a cross-currency transfer the user enters the amount sent (source currency) and the amount received (target currency) from their bank records, so the rate, spread, and fees are captured as they happened. Show the implied rate (for example, 1 SGD = 23.50 NTD) as a check. Same-currency transfers keep a single amount.
  - **Scope:**
    - Transfer API: accept an optional received amount, required when currencies differ and rejected or ignored when they match; accept a transfer date.
    - Transfer editing: today editing a PiggyBank transfer mirrors one amount onto both sides; cross-currency transfers need each side's amount edited separately while keeping the direction fixed.
    - Excel backup import: transfer-pair validation currently requires the two amounts to sum to zero; keep that for same-currency pairs, and for cross-currency pairs require one negative and one positive amount in banks of the two different currencies.
    - Frontend transfer form: allow targets of any currency, show a received-amount field and implied rate when the target's currency differs, and add a date field. Check the form on desktop and mobile.
    - Docs: update the transfer rules in `docs/architecture.md`, `docs/backlog.md`, and the `AGENTS.md` rule requiring matching currencies.
  - **Unchanged rules:** Both sides share one `transaction_id` and are created, edited, and deleted atomically; transfers stay excluded from income and spending totals; bank transfers (`transfer_out` / `transfer_in`) are unaffected.
  - **Acceptance:** A user can record an SGD → NTD transfer with both amounts and a past date; each PiggyBank's balance changes by its own amount; deleting either side removes both; Excel export then import round-trips the pair. API tests cover same-currency and cross-currency PiggyBank transfers, transfer editing, backup round-trip, and bank transfers.

- [ ] Bring the Type and Category select arrows closer to their labels in transaction forms.
  - **Scope:** Shared form styles on desktop and mobile.
  - **Acceptance:** Both controls remain legible and their arrow placement is visually consistent at narrow and wide widths.

- [ ] Add one themed dropdown component and use it for every select.
  - **Context:** Native selects such as the PiggyBank analytics metric picker ("Running Balance 💰") do not match the app's style.
  - **Scope:** A shared dropdown in `frontend/src/components/` using the tokens in `frontend/src/index.css`, with keyboard support (arrow keys, Enter, Escape, type-ahead) and a touch-friendly menu on mobile. Replace the analytics metric picker, Settings selects, and transaction form Type/Category selects. Later tasks (net worth currency, sort and filter controls) use it too.
  - **Decision:** Option labels are plain text with no emoji (for example, `Running Balance`, `Income / Deposits`, `Expenses / Withdrawals`). The open menu uses the app's colors and rounded panel style rather than the operating system's menu.
  - **Acceptance:** Every dropdown in the app looks consistent, has no emoji in its options, works with mouse, keyboard, and touch, and stays inside the viewport on mobile.

- [ ] Open Settings as a pop-up available from every page.
  - **Context:** Settings is currently a separate page (`/settings`) reached from the Dashboard.
  - **Scope:** A settings button in the shared page header on the Dashboard, PiggyBank view, and any later page opens a modal with the same sections (Profile, Display, Backup, Danger Zone). Closing it returns the user to the same page and scroll position; changes such as date format or transactions per page apply immediately to the page underneath. Keep `/settings` as a direct link that opens the same content.
  - **Acceptance:** Settings opens and closes from every page without navigation; focus is trapped in the modal and returns to the button on close; Escape and the backdrop close it; it is usable on desktop and mobile.

- [ ] Make the expense category chart scale to many categories.
  - **Context:** With many categories, the legend under the Expense Categories pie wraps into several rows and pushes into the chart.
  - **Scope:** Replace the inline legend with one compact control (for example, "18 categories") that opens a small panel on hover, focus, or tap. The panel lists every category vertically with its color, amount, and percentage, sorted largest first, and scrolls when long. Hovering or tapping a pie slice shows that category's name, amount, and percentage. Apply to both the Dashboard and PiggyBank analytics.
  - **Acceptance:** The pie keeps its size with 5 or 30 categories; every category's percentage is readable from the panel or the slice tooltip; percentages sum to 100% after rounding; works on desktop and mobile.

- [ ] Sort and filter transactions in a PiggyBank.
  - **Scope:** Controls above the transaction list: sort by date (default) or amount, ascending or descending; filter by one or more categories and by a date range (from and to, either optional, typed in the user's date format). Show the number of matching transactions and a clear-filters action. Paging (transactions per page) applies to the filtered result. PiggyBank analytics gets the same date range control.
  - **Acceptance:** Sorting and filtering update the list without reloading the page; the default view is newest first with no filters; filters reset when leaving the PiggyBank; an empty result shows a clear message; controls fit on mobile.

- [ ] Add direct page navigation to the PiggyBank transaction list.
  - **Context:** The list currently has Previous/Next controls and a `Page X of Y` label, but no way to select a numbered page or enter a page number.
  - **Scope:** Show up to five consecutive page buttons starting at the current page, shifting the window back near the end so five pages remain visible when available. For example, on page 12 of 46, show `< 12 13 14 15 16 … 46 >`; the last page is a direct shortcut after an ellipsis when it is outside the window. Highlight the current page. Add a labeled page-number input with a page-number placeholder; pressing Enter jumps to that page. Derive the maximum from the current total page count, including after the page-size setting or future filters change.
  - **Acceptance:** Clicking a page number or pressing Enter with an integer from 1 through the current last page changes the visible transactions; an empty, non-integer, below-1, or above-last-page entry shows an error and keeps the current page. Previous/Next remain available and disabled at their respective ends. Controls and error text are usable on desktop and mobile, including keyboard navigation.

- [ ] Convert balances between currencies for display, using fixed rates the user sets.
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
