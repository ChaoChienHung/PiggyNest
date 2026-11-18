# Backup identity and future synchronization

## Current behavior

The Excel backup is an add-only account export and import, not a two-way sync format. An exported numeric `entry_id` identifies a transaction within its source database. Import validates that ID inside the workbook, then assigns a fresh numeric database ID. It also remaps PiggyBank IDs and the shared UUID of each PiggyBank transfer. Thus two databases can both have transaction `id=7` without either row being overwritten by Excel import. If the destination user already has a PiggyBank with the same name, the whole import is rejected. It does not merge independent changes under that name.

The separate legacy CSV importer follows the same local-ID principle and holds unclear PiggyBank transfers for review. It is a one-time migration tool, not a sync engine.

## Shared backend configuration

Keep numeric IDs as local primary keys and API edit/delete handles. For everyday use on multiple devices, run **one** backend with one persistent database and point both devices at that API. All writes then use the same ID sequence and transfer constraints. Keep Excel export as a portable backup and restore path.

The frontend uses `VITE_API_BASE_URL` at build or development-server time; its default is `http://127.0.0.1:8000/api/v1`. Set it to the shared HTTPS API URL, including `/api/v1`, on each frontend installation. The CLI uses `PIGGYNEST_API_URL` at runtime with the same URL. CLI database inspection is local-only and disabled when a remote API is selected. The backend's `DATABASE_URL` must point to one persistent database volume; `SECRET_KEY` must be stable across restarts. Configure `ALLOWED_ORIGINS` with the exact browser origins as a JSON array, such as `["https://your-frontend.example"]`. Terminate TLS before the API, restrict direct database-file access, and use one writable backend instance for SQLite. These settings prepare the repo for a shared server; this repository does not provision a public host or transport security on its own.

Do not start separate writable copies of the database and assume they will merge. The backup importer still rejects same-name PiggyBanks and does not combine independent changes.

## Offline sync alternative

If offline editing and later merging become a product requirement, add a stable UUID to every PiggyBank and transaction. Keep the PiggyBank transfer's shared UUID as a separate logical operation ID. Export both stable and local IDs; on import, map by stable UUID and allocate local numeric IDs only for unseen objects. Importing the same backup again should be idempotent. A stable ID with different contents is a conflict to resolve, not an overwrite. Track revisions or an update timestamp with a base version, and record deletions as tombstones so an old backup cannot resurrect deleted transactions. Apply both sides of a PiggyBank transfer as one unit.

This is a proposed design only. Existing Excel files have no stable per-transaction UUID or deletion history, so they cannot safely provide full two-way synchronization. A migration and conflict-review UI would be needed before changing backup semantics.
