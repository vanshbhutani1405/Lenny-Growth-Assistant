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

## Durable sessions with bounded live context

PostgreSQL is the source of truth for session identifiers, ordered messages, timestamps, and provider/workflow metadata. `SessionManager` keeps bounded live provider context in memory for latency and Claude client reuse, evicts that optimization after 24 hours, and reconstructs it from PostgreSQL when needed. This preserves restart continuity without creating a second session system. Authentication and ownership remain future work.

## Bounded context

Transcript evidence and conversational history are bounded separately. This controls prompt size and prevents previous assistant text from becoming an accidental source.

## Rejected alternatives

- LangGraph: unnecessary for the current bounded workflows.
- Groq/OpenAI: outside the required provider scope.
- Another vector store: conflicts with the existing Supabase/pgvector design.
- WebSockets: unnecessary for server-to-browser token delivery.
- General web search: outside the PRD scope.
