# Engineering backlog

- Review ambiguous legacy transfers with `repair_transfer_ids.py`: link confirmed internal pairs or classify external entries. Automatic pairing only handles unique matches.
- Consider route-level service extraction when transaction workflows grow, and centralize shared authentication and ownership queries.
- Decide whether bank transfers need a dedicated counterparty field. Cross-currency PiggyBank transfers now store the actual sent and received amounts entered by the user; automatic exchange rates for display remain a separate decision.
- Earlier commits still contain SQLite databases (including the disposable Bob test account) and historical Python bytecode; `.gitignore` now ignores `__pycache__/` and `*.py[cod]` and tracked `.pyc` files have been removed from `HEAD`, but Git history still contains earlier copies. A history rewrite would need a separate coordinated decision.
- Verify email ownership at registration and provide shared gateway rate limits before deploying account recovery across multiple API workers.
- If offline multi-device editing is required, follow the stable-ID and conflict design in [data synchronization](data-sync.md); Excel backup is currently add-only.

See [engineering optimizations](engineering-optimizations.md) for completed backlog upgrades (Alembic migrations, configuration/legacy cleanup, frontend route-based code splitting, and bytecode cleanup).
