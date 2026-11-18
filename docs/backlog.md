# Engineering backlog

- Add versioned database migrations to replace startup `create_all` and inline `ALTER TABLE` logic.
- Migrate money from floating-point values to exact minor units or fixed decimals, including existing database and Excel backup conversions.
- Review ambiguous legacy transfers with `repair_transfer_ids.py`: link confirmed internal pairs or classify external entries. Automatic pairing only handles unique matches.
- Consolidate environment and YAML configuration. The current YAML file path and shipped YAML file differ.
- Decide whether the CSV/pandas bookkeeping modules and root CLI remain supported; update dependencies or remove them after that decision.
- Consider route-level service extraction when transaction workflows grow, and centralize shared authentication and ownership queries.
- Split the large frontend bundle by route if initial load performance becomes a concern.
- Decide whether external transfers need a dedicated counterparty field, and define currency conversion before allowing cross-currency internal transfers.
- Stop tracking generated Python bytecode and review the four committed SQLite databases before changing repository history; the development database currently supplies the documented local test account.
