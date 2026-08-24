# Lenny Growth Assistant backend

Milestone 1 provides the FastAPI, configuration, async SQLAlchemy, PostgreSQL/Alembic, and test foundation.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Set `DATABASE_URL`, `APP_ENV`, and `LOG_LEVEL` in `.env`. Apply the schema with `alembic upgrade head`.
