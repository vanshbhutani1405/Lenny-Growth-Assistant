# Technical Decisions

## PostgreSQL + pgvector

Transcript metadata and vector search remain in Supabase PostgreSQL. A second vector database would duplicate operational responsibility without improving this assignment.

## Local BGE embeddings

`BAAI/bge-small-en-v1.5` runs locally and produces 384-dimensional vectors. Query and corpus embeddings must use the same model for compatible cosine similarity.

## Provider-neutral workflows

Ollama enables a no-cloud local demo while Claude Agent SDK remains the production path. Shared tools and workflows prevent provider-specific RAG duplication.

## In-process MCP tools

Claude tools are registered through the SDK’s in-process MCP architecture. This preserves explicit schemas and avoids a separate tool service.

## SSE

SSE is sufficient for one-way token delivery and works naturally with the browser Fetch/ReadableStream client. Retrieval remains a completed prerequisite rather than an artificial stream.

## In-memory sessions

The 24-hour manager is intentionally small and fast for the assignment. The tradeoff is loss on backend restart and no authenticated ownership. Durable sessions are a clear next architectural step.

## Bounded context

Transcript evidence and conversational history are bounded separately. This controls prompt size and prevents previous assistant text from becoming an accidental source.

## Rejected alternatives

- LangGraph: unnecessary for the current bounded workflows.
- Groq/OpenAI: outside the required provider scope.
- Another vector store: conflicts with the existing Supabase/pgvector design.
- WebSockets: unnecessary for server-to-browser token delivery.
- General web search: outside the PRD scope.
