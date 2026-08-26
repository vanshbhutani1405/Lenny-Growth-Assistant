# Implementation notes

## Knowledge layer

Transcript loading is separated from normalization, chunking, embedding, and persistence. Chunk IDs are deterministic so ingestion can be safely retried. SQLAlchemy 2.x and Alembic keep the PostgreSQL schema explicit; pgvector stores 384-dimensional BGE embeddings. Ingestion persists bounded batches with PostgreSQL upsert semantics and explicit rollback handling.

The active query path uses a request-scoped `Retriever`, which generates a BGE query embedding and performs a vector-oriented database query with configured top-k, minimum score, and metadata filters. A separate `RetrievalService` provides hybrid keyword/semantic merging and one corrective attempt; this is retained as an independently testable capability and is not silently represented as active in every agent path.

## Agent boundary

`LennyAgent` owns orchestration, while tools adapt existing services to the Claude Agent SDK/MCP contract. The registry keeps tool names, schemas, descriptions, and registration centralized. Ollama and Claude implement the same provider-facing workflow shape, so local testing does not require changing the RAG layer.

## Durable sessions

The original live-session optimization remains, but PostgreSQL is now durable source of truth. `conversation_sessions` stores session metadata and timestamps; `conversation_messages` stores ordered user/assistant turns. `SessionManager` loads history before provider execution, bounds it before provider execution, persists successful turns, deletes cascaded data, and evicts only live provider context after 24 hours. Streaming writes the user turn at request start and writes the assistant turn only after successful completion.

## Streaming

SSE was chosen because the product streams generated text but does not need bidirectional transport. Retrieval completes first, then provider tokens are emitted as `token` events. Session/workflow context, sources, validation, completion, and errors use typed events that the frontend can handle incrementally.

## Frontend

The React/Vite client keeps a browser cache for responsive sidebar state but uses backend session list/detail/delete endpoints as the durable source. It renders Markdown, evidence cards, workflow badges, provider status, artifacts, loading states, and partial streams.

## Verification posture

This repository contains focused tests and compile/migration commands. Live database persistence, provider calls, LangSmith traces, and Docker runtime are environment-dependent and must be verified at submission time rather than inferred from source alone.
