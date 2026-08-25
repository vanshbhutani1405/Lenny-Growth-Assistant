# Lenny Growth Assistant

Lenny Growth Assistant is a transcript-grounded product and growth workspace. It searches the selected indexed Lenny podcast corpus, makes evidence inspectable, synthesizes themes, and turns grounded insights into Ship 30 writing and artifacts.

## Capabilities

- Hybrid semantic/keyword transcript retrieval with PostgreSQL + pgvector.
- Local `BAAI/bge-small-en-v1.5` embeddings at 384 dimensions.
- Grounded Q&A, Research & Synthesis, and Ship 30 workflows.
- Claude Agent SDK production path and local Ollama provider.
- Central tools for transcript search, Ship 30 validation, and artifact generation.
- 24-hour provider-neutral in-memory conversations.
- SSE token streaming with sources, validation, completion, and errors.
- Light React/Vite UI with markdown, evidence cards, workflow states, artifacts, browser history, and chat deletion.
- Optional LangSmith traces and structured operational logging.

## Architecture

See [architecture.md](architecture.md), [implementation.md](implementation.md), and [technical-decisions.md](technical-decisions.md). Add the final visual at `photos/architecture.png` when available.

## Stack

Python, FastAPI, Pydantic, SQLAlchemy 2.x, PostgreSQL/Supabase, pgvector, Alembic, pytest, React, Vite, Tailwind, Claude Agent SDK, Ollama, and optional LangSmith.

## Setup

Backend commands run from `backend/` with the project-local Python 3.11 environment. Copy `backend/.env.example` to `backend/.env`, configure the database/provider settings, apply Alembic migrations, and start the API with the existing Uvicorn command. Start the frontend with its existing Vite scripts.

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
- `DELETE /api/v1/agent/sessions/{session_id}`

Streaming emits `session`, `workflow`, `token`, `sources`, `validation`, `done`, and `error` SSE events.

## Documentation and demo

- [Manual testing plan](manual-testing.md)
- [Demo flow](demo.md)
- [Security notes](security.md)
- [Architecture](architecture.md)

Screenshots should be added under `photos/` when available.

## Limitations and future work

The current session manager is in-memory, expires after 24 hours, and is not authenticated or durable across backend restarts. The corpus is intentionally limited to the selected indexed episodes. Future work includes durable user-owned sessions, authentication, production artifact isolation verification, deployment automation, and a formal retrieval benchmark.
