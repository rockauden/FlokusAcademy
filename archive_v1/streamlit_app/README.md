# Flokus Academy v1 — Streamlit app (archived)

This is the original single-process Streamlit application. It is **not deployed
and not maintained**. The live system is the decoupled v2 stack:

- `backend/` — FastAPI, SQLAlchemy 2.0 async, Postgres, deployed at `api.flokusacademy.com`
- `frontend/` — Vue 3 + Vite, deployed at `app.flokusacademy.com`

It was kept at the repository root long after v2 replaced it, where its
`app.py`, `config.py` and `database.py` sat beside the real ones and made it
genuinely unclear which files the running system used. Moving it here answers
that question by looking at the directory tree.

Nothing in `backend/`, `frontend/` or CI references anything in this folder —
that was verified before the move.

## If you ever need to run it

It expects its own dependencies (`requirements.txt` here, not the backend's)
and reads the SQLite database `flokus.db`, which lives untracked at the
repository root and was left there deliberately: it holds real historical rows,
and moving a data file is a different decision from archiving code.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Note that it talks to SQLite directly and knows nothing about the tenancy,
migrations, XP ledger or safety layer that v2 added. Treat anything it shows
as historical.
