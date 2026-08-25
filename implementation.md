# Implementation Notes

## Why the boundaries exist

FastAPI routes handle validation and transport. RAG modules handle transcript retrieval. Provider adapters hide Ollama/Claude differences. The agent layer owns tool orchestration and workflow behavior. This keeps retrieval testable without an LLM and keeps providers replaceable without changing transcript indexing.

## Retrieval and grounding

The same local BGE model is used for corpus and query embeddings. pgvector provides cosine similarity, while PostgreSQL keyword search improves exact-term recall. Results carry source metadata into the final response. Context is bounded before generation, and empty/weak retrieval is handled explicitly.

## Agent tools

Tools are registered centrally and return structured data. `search_transcripts` delegates to the existing retriever rather than duplicating SQL or ranking logic. Ship 30 validation is bounded to one corrective redraft. Artifact generation is kept separate from retrieval.

## Provider switching

Ollama supports local development without an Anthropic key. Claude Agent SDK remains the production agent runtime. Both paths consume the same workflow concepts, source mappings, and session context.

## Sessions and history

The current implementation uses a 24-hour in-memory `SessionManager`. Claude retains one interactive client per active session; Ollama is passed bounded prior conversation turns. Fresh transcript retrieval remains independent from prior assistant prose.

## Streaming

SSE was chosen for one-way incremental generation over the existing HTTP API. Retrieval is deliberately not streamed. The client receives explicit lifecycle, token, source, validation, completion, and error events.

## Frontend

The frontend uses a light editorial layout with a sidebar, chat workspace, workflow states, markdown messages, source/evidence cards, Ship 30 artifact presentation, loading/error states, local browser history, and backend-backed deletion when a server session ID exists.

## Known scope boundary

The selected corpus is intentionally limited to the successfully indexed episodes. Durable PostgreSQL conversation persistence, authentication, multi-user ownership, and deployment automation are follow-up work unless separately added.
