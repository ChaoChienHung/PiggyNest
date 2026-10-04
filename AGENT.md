# PiggyNest development test account

Use **Bob** as the default account for manual feature testing in the local development app.

- Username: `Bob`
- Email / login: `bob@piggynest.test`
- Password: `BobTest2026!`
- Development database: `backend/data/bookkeeping.db` when the API is started from `backend/`

This is a disposable local test account. Keep manual test banks and transactions under Bob. Automated tests use their isolated test database, as configured in `backend/tests/conftest.py`. Do not use Bob's documented password for a deployed app.
