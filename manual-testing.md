# Manual end-to-end test plan

Record date, worktree state, provider, model, database target, and pass/fail for each case. Never record API keys, database passwords, or private URLs.

| ID | Scenario | Procedure | Expected result |
|---|---|---|---|
| QA-01 | Grounded Q&A | Ask a product/growth question | Answer is grounded, workflow badge is shown, sources are expandable |
| QA-02 | Follow-up | Ask a follow-up that refers to the previous turn | Same session understands conversational context and performs fresh transcript retrieval |
| QA-03 | Evidence | Inspect at least two source cards | Episode, guest, URL, chunk ID/index, excerpt, and score are visible where returned |
| QA-04 | Insufficient evidence | Ask for a fact outside the corpus | System explicitly says evidence is insufficient; no invented citation appears |
| SES-01 | Create/continue | Start without `session_id`, then submit another turn | A stable ID is returned and the second turn continues the session |
| SES-02 | Restart persistence | Complete a turn, restart backend, reload session from sidebar | PostgreSQL-backed session and ordered messages reload; provider live state may be reconstructed |
| SES-03 | Delete | Delete the active sidebar conversation | Backend DELETE succeeds, local state/messages disappear, and a new conversation starts |
| STR-01 | Streaming | Submit a normal QA request | Session/workflow events arrive, tokens render incrementally, then sources and done arrive |
| STR-02 | Partial failure | Stop/unavailable provider during a stream | Error is visible, partial text is handled gracefully, and no fake completed assistant turn is persisted |
| RES-01 | Research & Synthesis | Ask for cross-episode themes/comparisons | Structured synthesis preserves source attribution |
| SHIP-01 | Ship 30 | Request a Ship 30 draft | Draft appears as an artifact/document view with sources and validation status |
| SHIP-02 | Validation/redraft | Trigger a weak draft case | Validation issues are visible and at most one controlled redraft occurs |
| ART-01 | Artifact | Generate Markdown/HTML artifact and use copy/download | Output is complete and UI action works; treat HTML as untrusted |
| OPS-01 | Ollama outage/timeout | Stop Ollama or use an unreachable base URL | Structured provider error and useful backend log; UI remains usable |
| OPS-02 | Provider status | Open the app with Ollama and Claude configurations | Sidebar/header reflects backend-reported provider/model or shows the explicit fallback |
| OBS-01 | LangSmith | Configure tracing credentials and make one request | Trace shows API/workflow/tool/retrieval/provider/generation timing without secrets |
| API-01 | URL/CORS | Use browser devtools Network tab | Requests have one `/api` prefix, expected origin, and the ngrok warning header where configured |

## Evidence to collect

Capture sanitized screenshots of the main UI, evidence panel, Ship 30 artifact, streaming state, persisted sidebar session, and provider status. Add them under `photos/` only after behavior is demonstrated. Keep `architecture.png` as the architecture visual.
