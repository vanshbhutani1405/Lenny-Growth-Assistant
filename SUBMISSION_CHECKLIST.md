# Submission checklist

| Deliverable | Current status | Evidence / verification needed |
|---|---|---|
| FastAPI backend and versioned API | PRESENT | `backend/app/main.py`, `backend/app/api/v1/` |
| PostgreSQL + pgvector transcript data model | PRESENT | `backend/app/models/`, migrations `0001`/`0002` |
| Selected transcript corpus | PRESENT IN CODEBASE CONTEXT | Verify live row/episode counts on target DB; do not rerun ingestion |
| Semantic retrieval and source metadata | PRESENT | `backend/app/rag/retriever.py`, retrieval tests |
| Hybrid/corrective retrieval | PARTIAL | Service exists in `backend/app/rag/retrieval.py`; benchmark and active-agent wiring require confirmation |
| Claude Agent SDK | PRESENT IN CODEBASE | Verify provider credentials/API path in target environment |
| Ollama local provider | PRESENT IN CODEBASE | Verify Ollama model and timeout locally |
| Agent tools and workflows | PRESENT | `backend/app/agent/` |
| PostgreSQL conversation sessions/messages | PRESENT | models, `0003_conversation_sessions.py`, `SessionManager` |
| Session continuation after restart | IMPLEMENTED, LIVE UNVERIFIED | Apply migration and run manual restart test |
| SSE streaming | PRESENT | `/api/v1/agent/ask/stream`, frontend SSE client |
| Light frontend and evidence UI | PRESENT | `frontend/src/` |
| Provider status UI | PRESENT IN CODE | Verify live endpoint/frontend base URL alignment |
| Optional LangSmith tracing | PRESENT IN CODE | Verify trace visibility with credentials |
| Security boundaries | DOCUMENTED / PARTIAL IMPLEMENTATION | Review artifact isolation and authentication limitations |
| Automated tests | PRESENT IN REPOSITORY | Run with `backend.venv\\Scripts\\python.exe -m pytest` |
| Architecture image | PRESENT | `architecture.png` |
| Manual test plan and demo | PRESENT | `manual-testing.md`, `DEMO.md` |
| Deployment/Docker support | PRESENT IN FILES | Verify Docker Compose on target machine |

## Final verification commands

```powershell
cd backend
..\\backend.venv\\Scripts\\python.exe -m compileall -q app tests
..\\backend.venv\\Scripts\\python.exe -m pytest
..\\backend.venv\\Scripts\\python.exe -m alembic current
..\\backend.venv\\Scripts\\python.exe -m alembic upgrade head
```

Run the migration command only against the intended database. Never paste credentials into logs, screenshots, or transcripts.
