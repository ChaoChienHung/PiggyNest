# REVIEW

## Awaiting review

- [ ] Excel backup controls in Account Settings
  - **Delivered:** Replaced the exposed native file picker with matching Export Excel and Import Excel buttons in `frontend/src/pages/Settings.tsx` and `frontend/src/index.css`.
  - **Evidence:** `npm run build` and `npm run lint` passed; desktop and mobile screenshots showed no overflow, and the Import Excel button opened the file chooser in an isolated browser check.
  - **Review focus:** Confirm the button appearance and placement in Account Settings on desktop and mobile.

- [ ] Inline transaction editor
  - **Delivered:** Editing a transaction now opens its form directly below that transaction in `frontend/src/pages/PiggyBankView.tsx`, with responsive styles in `frontend/src/index.css`.
  - **Evidence:** Frontend build and lint passed; desktop and mobile checks confirmed the form appears immediately after the selected row, and a PiggyBank transfer remains editable through its paired transaction.
  - **Review focus:** Confirm that editing long transaction lists feels clear on desktop and mobile.
