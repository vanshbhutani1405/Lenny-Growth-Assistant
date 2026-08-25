# Manual Testing Plan

Run the backend and frontend with `LLM_PROVIDER=ollama` for the local path. Do not use production secrets in a local environment.

## Grounded QA and sources

1. Ask: “What does Lenny say about product-market fit?”
2. Confirm the workflow indicator is Grounded Q&A.
3. Confirm the answer is non-empty and source cards show episode, guest, title, chunk ID/index, URL, evidence, and similarity.
4. Expand a source and compare the claim with the displayed transcript evidence.
5. Ask an unsupported or highly specific question. Confirm the assistant explicitly says the available evidence is insufficient and does not fabricate citations.

## Follow-ups and sessions

1. Ask a first question, then ask “What examples did he give?” in the same session.
2. Confirm the second turn understands the conversation while performing fresh transcript retrieval.
3. Start a new conversation and verify it cannot see the previous session’s history.
4. Delete a conversation from the sidebar. Confirm the confirmation prompt, backend DELETE call, local removal, and active-chat reset.
5. Submit an unknown session ID and confirm a structured 404.
6. Verify the documented limitation that current in-memory sessions do not survive a backend restart.

## Streaming

1. Use the frontend or `POST /api/v1/agent/ask/stream`.
2. Confirm `session`, `workflow`, progressive `token`, `sources`, `done`, and any applicable `validation` events.
3. Stop Ollama during generation. Confirm an `error` event, an understandable UI error, and no false completed state.

## Research & Synthesis

Ask for common patterns across successful growth loops or compare advice from multiple episodes. Confirm structured sections, cross-episode evidence, and source attribution.

## Ship 30 and artifacts

1. Request a Ship 30 essay from grounded material.
2. Confirm hook, headings, skimmable prose, takeaways, validation status, and sources.
3. Confirm the UI supports copy and download actions where returned by the current artifact response.
4. Exercise a validation failure if available and confirm at most one controlled redraft.
5. Request an artifact and verify Markdown/HTML presentation, preview/code behavior, and safe failure handling. Treat generated HTML as untrusted.

## Dependency failures

Use an unreachable Ollama URL or stop the local service. Confirm timeout/provider errors are actionable. Exercise empty retrieval and a database outage in a safe environment to verify structured errors.

## LangSmith

With credentials configured, inspect traces for request, workflow, retrieval, tool calls, provider/model, latency, generation, sources, validation, artifact work, and errors. Remove credentials and verify the application still runs normally.
