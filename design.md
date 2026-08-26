# Product and interaction design

## Product principle

Lenny Growth Assistant is an evidence-first workspace, not a generic chatbot. The interface makes the answer readable, the workflow visible, and the transcript passages inspectable without overwhelming the user.

## Visual language

The frontend uses a light editorial system: warm white surfaces, restrained blue accents, thin borders, compact shadows, strong typographic hierarchy, and generous reading width. Motion is limited to loading and streaming feedback. The layout is desktop-first but collapses into a usable single-column view on small screens.

## Primary surfaces

- **Sidebar:** brand, new conversation, persisted session history, workflow cues, and delete controls.
- **Conversation workspace:** user/assistant turns, Markdown rendering, workflow badge, and streaming status.
- **Evidence panel:** expandable source cards with episode, guest, URL, chunk, similarity, and transcript excerpt.
- **Artifact card:** Markdown/Ship 30 output with validation state and copy/download actions where supported.
- **Provider status:** backend-reported Ollama/Claude provider and model; unavailable status is shown without breaking the app.

## Interaction rules

- Enter submits; Shift+Enter creates a newline.
- Streaming appends token events and keeps useful partial output if a connection fails.
- Sources arrive as a final SSE event and remain attached to the assistant turn.
- A new conversation clears only the active browser context; deleting a persisted session calls the backend DELETE endpoint and removes local state.
- Empty evidence and provider/database failures use explicit, recoverable error states rather than fabricated content.

## Accessibility and trust

Controls use visible labels or accessible names, status changes are text-visible, and evidence is visually separated from generated prose. The UI does not present conversation history as transcript evidence.
