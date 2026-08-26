# Lenny Growth Assistant

Lenny Growth Assistant is a transcript-grounded product and growth workspace. It searches a selected indexed Lenny podcast corpus, makes evidence inspectable, synthesizes themes, and turns grounded insights into Ship 30 writing and artifacts.

## Capabilities

- Semantic transcript retrieval with PostgreSQL + pgvector; a separate hybrid/corrective retrieval service is also implemented for continued evaluation.
- Local `BAAI/bge-small-en-v1.5` embeddings at 384 dimensions.
- Grounded Q&A, Research & Synthesis, and Ship 30 workflows.
- Claude Agent SDK production path and local Ollama provider.
- Central tools for transcript search, Ship 30 validation, and artifact generation.
- PostgreSQL-backed conversation sessions/messages with a 24-hour in-memory execution-context optimization.
- SSE token streaming with sources, validation, completion, and errors.
- Light React/Vite UI with markdown, evidence cards, workflow states, artifacts, browser history, and chat deletion.
- Optional LangSmith traces and structured operational logging.

## Architecture

See [architecture.md](architecture.md), [design.md](design.md), [implementation.md](implementation.md), and [technical-decisions.md](technical-decisions.md). The current architecture visual is [architecture.png](architecture.png).

## Stack

Python, FastAPI, Pydantic, SQLAlchemy 2.x, PostgreSQL/Supabase, pgvector, Alembic, pytest, React, Vite, Tailwind, Claude Agent SDK, Ollama, and optional LangSmith.

## Setup

Backend commands run from `backend/` with the project-local Python 3.11 environment (`backend.venv\\Scripts\\python.exe` on Windows). Copy `backend/.env.example` to `backend/.env`, configure the database/provider settings, apply Alembic migrations, and start the API with Uvicorn. Start the frontend with its existing Vite scripts.

The selected transcript corpus is already indexed. Do not run ingestion as part of application startup.

## Ollama local path

Run Ollama locally and make the configured model available:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
OLLAMA_TIMEOUT_SECONDS=300
```

The cloud path uses `ANTHROPIC_API_KEY` and `CLAUDE_MODEL`. Provider switching does not require RAG or workflow changes.

## Environment

Required core settings include `DATABASE_URL`, `APP_ENV`, and `LOG_LEVEL`. Optional tracing settings are:

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=lenny-growth-assistant
```

See `backend/.env.example` for the complete configuration. Keep secrets in local environment files; never expose them to the frontend.

## API

- `GET /health`
- `GET /health/db`
- `POST /api/v1/retrieval/search`
- `POST /api/v1/agent/ask`
- `POST /api/v1/agent/ask/stream`
- `GET /api/v1/agent/sessions`
- `GET /api/v1/agent/sessions/{session_id}`
- `DELETE /api/v1/agent/sessions/{session_id}`

Streaming emits `session`, `workflow`, `token`, `sources`, `validation`, `done`, and `error` SSE events.

## Running with Docker

Docker Compose builds the FastAPI backend and the production nginx frontend. The backend runs Alembic migrations before starting Uvicorn.

1. Copy `backend/.env.example` to `backend/.env` and set `DATABASE_URL`.
2. For local Ollama, use:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2:1b
OLLAMA_TIMEOUT_SECONDS=300
FRONTEND_ORIGIN=http://localhost:3000
```

Ollama runs outside the backend container on the host. Docker Compose provides `host.docker.internal` for the container-to-host connection. For Claude, use `LLM_PROVIDER=claude`, set `ANTHROPIC_API_KEY`, and configure `CLAUDE_MODEL` instead.

The frontend API origin is configured at build time with `VITE_API_BASE_URL` and defaults to `http://localhost:8000`:

```powershell
$env:VITE_API_BASE_URL = "http://localhost:8000"
docker compose up --build
```

Open the frontend at [http://localhost:3000](http://localhost:3000). The backend and API documentation are available at [http://localhost:8000](http://localhost:8000) and [http://localhost:8000/docs](http://localhost:8000/docs). Stop the stack with:

```powershell
docker compose down
```

Required backend configuration includes `DATABASE_URL`, `APP_ENV`, `LOG_LEVEL`, provider settings, and any required Claude/LangSmith variables. Secrets belong in `backend/.env`, not Dockerfiles or frontend build variables.

## Documentation and demo

- [Manual testing plan](manual-testing.md)
- [Demo flow](demo.md)
- [Submission checklist](SUBMISSION_CHECKLIST.md)
- [Development-log summaries](agent_transcripts/README.md)
- [Security notes](security.md)
- [Architecture](architecture.md)

The architecture image is included at the repository root as `architecture.png`. Additional UI screenshots may be added under `photos/` when available.

## Limitations and future work

The selected corpus is intentionally limited to the indexed episodes. Session records and messages are persisted in PostgreSQL by the current implementation, while live provider clients and bounded execution context are in memory and expire after 24 hours. There is no authentication or user ownership boundary yet. The active agent path uses semantic retrieval; hybrid/corrective retrieval is implemented as a separate service and should be wired into the production path after benchmarked evaluation. Future work includes authentication, artifact isolation verification, deployment automation, and a formal retrieval benchmark.

## Verification status

The repository contains automated tests and operational verification commands, but claims about the live Supabase database, Ollama availability, Claude credentials, LangSmith traces, and Docker runtime should be re-run on the target machine before submission. See [manual-testing.md](manual-testing.md) and [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md).
