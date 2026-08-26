# Ingestion summary

The ingestion work established Markdown/frontmatter loading, normalization, deterministic episode/chunk identity, configurable word chunking, local `BAAI/bge-small-en-v1.5` embeddings, 384-dimensional pgvector storage, bounded batch persistence, explicit rollback, and progress logging. The corpus source contains 303 episode files; the intentionally selected indexed dataset is reported as approximately 143 episodes and 6,500 chunks. This summary does not claim a fresh full-corpus run.
