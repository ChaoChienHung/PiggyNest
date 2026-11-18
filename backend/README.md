# PiggyNest backend

Start from this directory so the default SQLite database resolves to `data/piggynest.db`:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run the isolated API tests with `venv/bin/python -m pytest tests -q` from this directory.

Engineering documentation lives in [`../docs/`](../docs/README.md), including [architecture](../docs/architecture.md) and [technology stack](../docs/tech-stack.md).
