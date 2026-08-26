# Security

## Grounding boundary

Retrieved transcript text is untrusted evidence. It must not override system instructions or tool policy. Claims should be supported by returned chunks, with explicit insufficiency when evidence is weak.

## Transcript-source trust

Source metadata is preserved for traceability, not treated as authorization. URLs and transcript content should be displayed as data. The system does not grant retrieved text permission to execute code or invoke tools.

## Artifact sanitization

Model-generated HTML is untrusted. Production rendering must sanitize dangerous markup and/or isolate the preview in a restricted sandbox. Raw HTML should not be injected into the application DOM without an explicit policy. Markdown is user-visible content, not executable content.

## Provider and key handling

Anthropic and LangSmith keys are backend-only environment variables. Never expose them through Vite variables, API responses, logs, source cards, or generated artifacts. Ollama’s local URL/model are configuration, not secrets.

## Session limitations

Session identifiers and conversation messages are persisted in PostgreSQL, while live provider clients and bounded execution context remain in memory and expire after 24 hours. There is no authentication or user ownership check, so a session ID is not a security boundary. The current design is appropriate for a local/internal assignment prototype, not a multi-tenant deployment.

## Errors and logging

Use structured errors for retrieval, provider, database, stream, and artifact failures. Logs should include operational identifiers and latency but never API keys or full transcript contents. A failed stream must not be presented as a successful completed answer.

## Production follow-up

Before deployment, add authentication/authorization, rate limiting, secret management, retention controls, durable session ownership, CSP/sandbox verification, and formal artifact security tests.
