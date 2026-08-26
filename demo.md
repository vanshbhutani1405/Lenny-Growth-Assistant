# Three-to-five minute demo

## Before the demo

1. Start PostgreSQL/Supabase with the selected transcript data and apply migrations.
2. Start Ollama with `llama3.2:1b`, or configure Claude with a valid backend-only key.
3. Start the backend and frontend. Confirm the provider indicator reports the configured backend provider.
4. Open the browser with LangSmith tracing enabled only if credentials are available.

## Flow

1. **Grounded Q&A (45 seconds):** Ask, “What does Lenny say about product-market fit?” Show the concise answer, workflow badge, streamed tokens, and expandable evidence cards. Open one source URL and point out episode, guest, chunk, and similarity metadata.
2. **Follow-up (30 seconds):** Ask, “What examples did he give?” in the same session. Show that the session continues while transcript evidence is retrieved for the new turn.
3. **Research & Synthesis (45 seconds):** Ask for recurring patterns in onboarding or growth across several guests. Highlight structured themes and source attribution.
4. **Ship 30 (60 seconds):** Request a Ship 30-style essay on one grounded product lesson. Show validation status, the artifact card, and copy/download actions. Explain that validation allows at most one controlled redraft.
5. **Persistence and deletion (30 seconds):** Refresh the page or restart the backend, reload the session from the sidebar, then delete it and show the empty/new conversation state.
6. **Resilience and observability (30 seconds):** Briefly show the provider status, an insufficient-evidence response, and the LangSmith trace if configured. If Ollama is unavailable, show the structured failure state rather than hiding it.

Do not claim live provider, database, LangSmith, or Docker behavior unless it was verified in the demo environment.
