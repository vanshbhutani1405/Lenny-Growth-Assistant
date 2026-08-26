# Streaming and frontend summary

The API exposes SSE streaming for session, workflow, token, sources, validation, done, and error events. Ollama streams generated output through its chat interface; retrieval is completed before tokens begin. The React frontend incrementally renders tokens, stores browser session state, loads/deletes persisted sessions, displays workflow badges and evidence cards, and presents artifacts and provider status.
