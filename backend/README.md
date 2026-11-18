# PiggyNest backend

Start from this directory. The default SQLite database lives in the repository's Git-ignored `data/piggynest.db`, independent of the process's working directory:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API creates the local database on first startup. It is ignored by Git. Register the disposable Bob test account through the frontend if it is not present yet; see the root README for its credentials.

For account recovery email, copy `.env.example` to `.env` and configure a TLS SMTP server. Recovery requests return 503 while mail is unconfigured. See [account recovery](../docs/account-recovery.md) for the full behavior and security limits.

Run the isolated API tests with `venv/bin/python -m pytest tests -q` from this directory.

Engineering documentation lives in [`../docs/`](../docs/README.md), including [architecture](../docs/architecture.md) and [technology stack](../docs/tech-stack.md).
