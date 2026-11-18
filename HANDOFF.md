# Handoff

## Snapshot

- Updated: 2026-11-18. Branch: `main`.
- Stopping point: The Settings page's Excel import control is now a regular button that opens a hidden file input. Export and import buttons align on desktop and fill the card width on narrow screens. `cd frontend && npm run build && npm run lint` passed. An isolated test account confirmed the desktop and mobile layouts, no horizontal overflow, and that Import Excel opens the file chooser.
- Working tree: Clean after the UI change and this handoff were pushed. Verify with `git status --short` before starting new work.
- Local data: `data/piggynest.db` is ignored by Git. The local database contains the Ludwig records, including transaction 346 restored to LudwigSingapore (SGD); it is not part of the push.

## In-progress work

None.
