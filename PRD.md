# PRD — The Lenny Growth Assistant

**Status:** Implementation-ready  
**Purpose:** Product and system requirements for the FDE take-home assignment

---

## 1. Product Overview

### Product
**The Lenny Growth Assistant** is a full-stack conversational AI application that turns Lenny’s Podcast transcripts into a reliable internal knowledge assistant.

The product enables users to:

1. Ask product-management and growth questions grounded strictly in Lenny’s transcript corpus.
2. Continue conversations with independent session context.
3. Turn grounded answers into Ship 30 for 30–style essays.
4. Generate Markdown or HTML/CSS artifacts and view them directly beside the chat.
5. Run the same agent workflow with either Anthropic Claude or a local Ollama model.

The assignment explicitly frames this as a forward-deployment engagement: the solution should be understandable, runnable, testable, trustworthy, and extensible by another team.

## 2. Problem Statement

A product and growth team has access to a large collection of Lenny’s Podcast transcripts but cannot efficiently turn that corpus into reliable, reusable knowledge.

The assistant must remove the need for users to understand prompts, models, retrieval infrastructure, or implementation details while maintaining a high standard of grounding.

The core problems are:

- Finding relevant advice across a large transcript corpus.
- Answering questions without hallucinating beyond the available material.
- Preserving context across follow-up questions.
- Reusing grounded knowledge as structured written content.
- Producing useful rendered artifacts without sending users to another application.
- Providing a local model path that can be demonstrated through Ollama.
- Leaving behind a system another engineer can operate and extend.

## 3. Target User

### Primary user

A product, growth, strategy, or related team member who wants to quickly extract and reuse insights from Lenny’s Podcast.

### User characteristics

The user should not need to know:

- How RAG works.
- Which model is running.
- How transcripts are indexed.
- How prompts are structured.
- How artifacts are rendered.

The product should expose useful outcomes rather than infrastructure complexity.

## 4. Goals

### Product goals

- Provide reliable, transcript-grounded answers.
- Support contextual follow-up conversations.
- Make evidence visible through source citations.
- Generate reusable Ship 30 for 30–style content from grounded answers.
- Generate Markdown and HTML/CSS artifacts inside the product.
- Make cloud/local model selection transparent.
- Provide graceful behavior when evidence, models, or dependencies are unavailable.

### Engineering goals

- Use FastAPI for the backend.
- Use the Anthropic Claude Agent SDK for the agent layer.
- Use Anthropic Claude as the cloud model.
- Use Ollama for local execution.
- Persist application data in PostgreSQL through Supabase.
- Use pgvector for semantic retrieval.
- Use local BAAI/bge-small-en-v1.5 embeddings.
- Use Hybrid RAG combining semantic and keyword retrieval.
- Make retrieval, agent behavior, model calls, and failures observable.
- Keep the system reproducible and easy to hand off.

## 5. Non-Goals

The following are intentionally outside scope:

- Building a general-purpose ChatGPT competitor.
- Supporting arbitrary external knowledge sources at runtime.
- Training or fine-tuning an LLM.
- Building a research-grade Self-RAG implementation.
- Introducing multiple vector databases.
- Introducing multiple observability platforms.
- Building a complex multi-service distributed architecture.
- Adding unnecessary authentication or enterprise identity systems.
- Supporting many cloud model providers beyond the required Anthropic path.
- Building a sophisticated evaluation platform.

The priority is a reliable, polished assignment solution rather than maximum architectural complexity.

## 6. Success Metrics

### Primary success metric

**Grounded answer rate:** At least **90% of benchmark questions** should produce final answers supported by relevant transcript evidence.

This is a target, not a claimed achieved result.

### Secondary metrics

- Retrieval hit rate on the evaluation set.
- Correct detection of unsupported/out-of-corpus questions.
- Successful artifact generation rate.
- Successful provider switching.
- Session-isolation correctness.
- Successful local Ollama execution.
- API/model/retrieval failure recovery.

## 7. Assumptions

- The provided Lenny’s Podcast / Newsletter transcript repository is the authoritative knowledge source.
- The assignment corpus is sufficiently complete for the intended product and growth questions.
- Supabase PostgreSQL is used as managed PostgreSQL infrastructure.
- pgvector is available/enabled in the Supabase project.
- BAAI/bge-small-en-v1.5 is run locally for embedding generation.
- The exact Ollama model is selected based on the developer’s available laptop resources.
- Anthropic credentials are available for cloud execution.
- The evaluator can configure external services using documented environment variables.
- The application is primarily an evaluation/internal prototype rather than a public multi-tenant SaaS product.

## 8. Scope

### In scope

- Transcript ingestion and indexing.
- Transcript metadata and source traceability.
- Hybrid semantic + keyword retrieval.
- Lightweight corrective retrieval.
- Grounding validation.
- Conversational sessions.
- Anthropic Claude execution.
- Ollama execution.
- Visible provider/model selection.
- Three dedicated agent skills.
- Ship 30 validation and one controlled redraft.
- Markdown/HTML artifact generation.
- Safe artifact rendering.
- LangSmith observability.
- Structured operational logging.
- Automated tests.
- Small RAG evaluation benchmark.
- Reproducible application startup.

### Out of scope

- General web search.
- User-generated knowledge-base ingestion during the evaluation.
- Fine-tuning.
- Complex long-term memory beyond persisted session context.
- Production-scale multi-region infrastructure.
- Advanced access-control systems.
- Multiple cloud providers.

## 9. User Flows

### 9.1 Grounded Q&A

1. User opens the application.
2. User starts a new session or selects an existing session.
3. User enters a product/growth question.
4. Agent identifies the Grounded QA skill.
5. Query is processed.
6. Hybrid retrieval searches semantic and keyword indexes.
7. Results are merged/ranked.
8. Retrieval relevance is checked.
9. If evidence is insufficient, one corrective query/retrieval attempt is performed.
10. Grounded context is supplied to Claude/Ollama.
11. The response is validated for grounding.
12. User receives the answer with identifiable/clickable transcript sources.

### 9.2 Follow-up conversation

1. User asks a follow-up within the same session.
2. Previous session messages are loaded.
3. The new question is interpreted using the session context.
4. Retrieval is performed against the transcript corpus.
5. The answer is generated using both relevant session context and transcript evidence.
6. The response remains isolated from other sessions.

### 9.3 Unsupported question

1. User asks something not sufficiently supported by the transcript corpus.
2. Retrieval returns weak/empty evidence.
3. The system attempts one corrective retrieval.
4. If evidence remains insufficient, the assistant explicitly says that the available material does not support a reliable answer.
5. The system must not invent an answer.

### 9.4 Ship 30 essay

1. User asks the assistant to turn grounded material into a Ship 30 for 30–style essay.
2. Agent invokes the dedicated Ship 30 skill.
3. The skill uses grounded transcript evidence.
4. Draft is generated at approximately 1,250 words.
5. Automated checks validate structure/style requirements.
6. If validation fails, the skill performs one controlled redraft.
7. Final essay is returned.

Required characteristics include:

- Strong hook.
- Clear narrative progression.
- Headings.
- Skimmable paragraphs.
- Bullets where useful.
- Selective bold emphasis.
- Specific useful takeaway.
- Claims grounded in the transcript corpus.

### 9.5 Artifact generation

1. User requests a document/webpage/artifact based on the current conversation.
2. Agent invokes Artifact Generation.
3. Markdown or complete HTML/CSS is generated.
4. Generated HTML is treated as untrusted.
5. Dangerous content is sanitized or isolated.
6. Artifact is displayed in the Artifact Viewer beside the chat.
7. User can switch between rendered Preview and Code.

### 9.6 Provider switching

1. User sees the currently active provider/model.
2. User switches between Anthropic and Ollama.
3. The application routes subsequent model calls through the selected provider.
4. The agent skills and RAG system remain unchanged.
5. Provider/model failures are surfaced with actionable errors.

## 10. Functional Requirements

### FR-01 — FastAPI API

The backend MUST use FastAPI.

It MUST provide:

- Clear request/response schemas.
- Input validation.
- Structured errors.
- Health/dependency endpoints.

### FR-02 — Agent runtime

The agent layer MUST use the Anthropic Claude Agent SDK.

The architecture MUST maintain clear boundaries between:

- Agent routing.
- Skills.
- Retrieval.
- Model execution.
- Persistence.

### FR-03 — Sessions

Users MUST be able to:

- Start a new chat.
- Continue an existing chat.
- Maintain independent session context.

Messages from one session MUST NOT leak into another session.

### FR-04 — Persistence

PostgreSQL MUST persist at minimum:

- Session identifiers.
- Messages.
- Timestamps.
- User/session metadata as applicable.

Supabase PostgreSQL is the selected database.

### FR-05 — Cloud model

Anthropic Claude MUST be supported as the cloud model.

### FR-06 — Local model

Ollama MUST be supported and MUST be demonstrated locally.

The selected Ollama model MUST be practical for the developer’s machine.

### FR-07 — Provider visibility

The selected provider/model MUST be visible in the UI or configuration.

Fallback behavior MUST be documented.

### FR-08 — Knowledge ingestion

The system MUST:

- Load the supplied transcript corpus.
- Clean/normalize transcripts.
- Chunk transcripts.
- Generate embeddings locally.
- Store chunks and metadata.
- Store vectors in pgvector.
- Support safe/idempotent re-ingestion.
- Preserve source traceability.

### FR-09 — Retrieval

The retrieval system MUST combine:

- Semantic vector retrieval using pgvector.
- PostgreSQL keyword/full-text retrieval.

The system MUST merge/rank candidates before generation.

### FR-10 — Corrective retrieval

If initial retrieval is insufficient, the system SHOULD perform one lightweight query-rewrite/retrieval attempt before declaring the corpus insufficient.

It MUST avoid unbounded retrieval loops.

### FR-11 — Grounding

Generated answers MUST be based on relevant transcript evidence.

The UI MUST identify supporting sources.

The system MUST explicitly acknowledge insufficient evidence.

### FR-12 — Ship 30 skill

The Ship 30 skill MUST be implemented as a dedicated skill/tool.

It MUST encode the relevant writing principles instead of relying on one unstructured prompt.

It MUST include an automated validation step and at most one corrective redraft.

### FR-13 — Artifact generation

The system MUST generate:

- Markdown documents.
- Complete HTML/CSS artifacts.

Artifacts MUST render in-app beside the conversation.

### FR-14 — Artifact security

Generated HTML MUST be treated as untrusted.

The implementation MUST use an appropriate sanitization and/or isolation strategy.

The security boundary MUST document:

- What content is permitted.
- What content is blocked.
- Why the restrictions exist.

### FR-15 — Observability

LangSmith MUST provide AI/agent tracing and debugging visibility.

Structured application logs MUST provide enough information to diagnose:

- Model failures.
- Retrieval failures.
- Database failures.
- Artifact failures.
- Provider failures.

### FR-16 — Resilience

The system MUST handle gracefully:

- Missing API keys.
- Unavailable Ollama.
- Model timeouts.
- Empty retrieval results.
- Database connection failures.

Errors SHOULD be actionable and understandable to the user/developer.

## 11. Agent & Skill Requirements

### Grounded QA

Responsibilities:

- Interpret the user's question.
- Use the retrieval pipeline.
- Maintain session context.
- Answer only from available evidence.
- Identify supporting sources.
- Refuse/qualify unsupported claims.

### Ship 30

Responsibilities:

- Transform grounded material into the required essay format.
- Preserve factual grounding.
- Validate word count and structural requirements.
- Correct its own failed draft once.

### Artifact Generation

Responsibilities:

- Transform conversation-derived information into Markdown or HTML/CSS.
- Mark artifacts clearly for frontend rendering.
- Never bypass artifact security controls.

## 12. RAG / Knowledge Requirements

### Ingestion pipeline

Conceptually:

```text
Transcript repository
        ↓
Load + normalize
        ↓
Chunk
        ↓
BGE-small embeddings
        ↓
Supabase PostgreSQL
        ↓
pgvector + keyword index
```

Each chunk SHOULD preserve metadata such as:

- Episode slug.
- Guest.
- Title.
- YouTube URL.
- Publish date.
- Chunk identifier/index.

### Retrieval pipeline

```text
User query
   ↓
Query processing
   ↓
 ┌─────────────────────┐
 │                     │
Vector retrieval    Keyword retrieval
 │                     │
 └──────────┬──────────┘
            ↓
       Merge / rank
            ↓
      Relevance check
            ↓
     Corrective retry?
        /              yes        no
       ↓          ↓
   retrieve     generate
       ↓          ↓
       └──────┬───┘
              ↓
      Grounding validation
              ↓
       Answer + sources
```

The system should favor correctness and transparency over retrieval complexity.

## 13. Model & Provider Requirements

### Anthropic

- Cloud execution path.
- Used through the Claude Agent SDK.
- API credentials supplied through environment configuration.

### Ollama

- Local execution path.
- Model configurable through environment configuration.
- Must be tested on the developer’s machine before the demo.

### Provider abstraction

Provider-specific implementation details MUST remain behind a common application interface where practical.

Switching providers MUST NOT require rewriting the RAG or skill logic.

## 14. Data & Persistence Requirements

Core logical entities:

### sessions

- `id`
- `created_at`
- `updated_at`
- optional metadata

### messages

- `id`
- `session_id`
- `role`
- `content`
- `created_at`
- optional metadata/source references

### transcript_chunks

- `id`
- `episode_slug`
- `guest`
- `title`
- `youtube_url`
- `publish_date`
- `chunk_index`
- `chunk_text`
- `embedding`

The exact vector dimension MUST be derived from the installed embedding model rather than assumed.

Database constraints and indexes SHOULD support:

- Session lookups.
- Message ordering.
- Vector similarity retrieval.
- Keyword/full-text retrieval.
- Deterministic ingestion.

## 15. Artifact & Security Requirements

Artifact rendering is a trust boundary.

The system MUST:

- Treat model-generated HTML as untrusted.
- Sanitize dangerous HTML where appropriate.
- Prevent arbitrary script execution from escaping the artifact sandbox.
- Avoid exposing backend secrets to generated content.
- Render artifacts in an isolated browser context.
- Keep the security policy simple enough for an evaluator to understand.

The Artifact Viewer MUST provide:

- Preview.
- Code.
- Clear artifact state.
- Useful error handling when rendering fails.

## 16. Observability & Resilience

### LangSmith

Use LangSmith to inspect:

- Agent execution.
- Skill routing.
- Model calls.
- Retrieval steps.
- Latency.
- Failures.
- Debugging/evaluation traces.

### Application logs

Structured logs SHOULD include:

- Request ID.
- Session ID.
- Provider.
- Model.
- Retrieval latency.
- Generation latency.
- Relevant retrieval metadata.
- Error category.
- Dependency status.

Logs MUST NOT contain API keys or other secrets.

## 17. UI/UX Requirements

The application should present the product as a simple internal assistant rather than exposing implementation complexity.

### Main experience

- Chat interface.
- Session controls.
- Visible provider/model.
- Streaming/loading state where supported.
- Source citations.
- Artifact Viewer beside chat.

### States

The UI MUST clearly handle:

- Empty state.
- Loading state.
- Streaming state.
- Successful response.
- No relevant evidence.
- Provider failure.
- Ollama unavailable.
- Artifact generation failure.
- Artifact rendering failure.

### Responsive behavior

On narrower screens, the chat and artifact areas SHOULD stack or otherwise remain usable rather than becoming unreadably narrow.

### Accessibility

The UI SHOULD support:

- Keyboard-accessible controls.
- Clearly labeled interactive elements.
- Sufficient visual contrast.
- Accessible status/error messaging.
- Semantic structure.

## 18. Acceptance Criteria

### Conversational assistant

- [ ] User can create a new session.
- [ ] User can continue an existing session.
- [ ] Session context remains isolated.
- [ ] Product/growth questions retrieve relevant transcript material.
- [ ] Answers identify supporting sources.
- [ ] Unsupported questions receive an explicit evidence limitation.
- [ ] No unbounded corrective retrieval loops occur.

### Agent/skills

- [ ] Claude Agent SDK is the agent runtime.
- [ ] Grounded QA is a dedicated skill.
- [ ] Ship 30 is a dedicated skill.
- [ ] Artifact generation is a dedicated skill.
- [ ] Ship 30 validation works.
- [ ] Failed Ship 30 drafts can trigger one controlled redraft.

### Models

- [ ] Anthropic cloud execution works.
- [ ] Ollama local execution works.
- [ ] Provider/model selection is visible.
- [ ] Provider failures produce actionable messages.

### Knowledge base

- [ ] Transcript ingestion works.
- [ ] Embeddings are generated locally.
- [ ] pgvector retrieval works.
- [ ] Keyword retrieval works.
- [ ] Hybrid retrieval produces ranked candidates.
- [ ] Source metadata is preserved.

### Artifacts

- [ ] Markdown generation works.
- [ ] HTML/CSS generation works.
- [ ] Artifacts render beside the chat.
- [ ] Code view is available.
- [ ] Unsafe HTML is sanitized or isolated.
- [ ] Rendering failures are handled safely.

### Operations

- [ ] Health checks are available.
- [ ] Structured logs are available.
- [ ] LangSmith tracing is configured.
- [ ] Missing keys are handled.
- [ ] Ollama outage is handled.
- [ ] Model timeout is handled.
- [ ] Empty retrieval is handled.
- [ ] Database failure is handled.

## 19. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Hallucinated answers | High | Hybrid retrieval, relevance checks, grounding validation, explicit unsupported-answer behavior |
| Weak retrieval | High | Semantic + keyword retrieval and one corrective retrieval attempt |
| Local model quality | Medium | Use a model that runs comfortably on the machine; validate key flows locally |
| Local model latency | Medium | Keep local model configurable and use clear loading states |
| Cloud/API cost | Medium | Keep requests scoped, use local embeddings, avoid unnecessary model calls |
| Database failure | High | Health checks, structured errors, actionable failure states |
| Ollama unavailable | High | Dependency check and visible provider-switch guidance |
| Unsafe generated HTML | High | Sanitization and sandboxed/isolation strategy |
| Cross-session leakage | High | Session-scoped persistence and explicit isolation tests |
| Duplicate ingestion | Medium | Deterministic identifiers/idempotent ingestion |
| Observability gaps | Medium | LangSmith traces + structured operational logs |
| Scope creep | Medium | Explicit non-goals and fixed three-skill architecture |

## 20. Implementation Plan

### Phase 1 — Foundation

- Create repository structure.
- Configure FastAPI.
- Configure Supabase PostgreSQL.
- Define database models and migrations.
- Add configuration management.
- Add health endpoints.

### Phase 2 — Knowledge ingestion

- Load transcript repository.
- Normalize and chunk transcripts.
- Generate local BGE embeddings.
- Store chunks and vectors.
- Add PostgreSQL keyword/full-text retrieval.
- Make ingestion deterministic and repeatable.

### Phase 3 — RAG

- Implement semantic retrieval.
- Implement keyword retrieval.
- Implement hybrid ranking.
- Add relevance validation.
- Add one corrective retrieval attempt.
- Add grounding/source metadata.

### Phase 4 — Agent

- Integrate Claude Agent SDK.
- Implement Grounded QA skill.
- Implement Ship 30 skill.
- Implement Artifact Generation skill.
- Connect skills to the RAG and artifact subsystems.

### Phase 5 — Provider support

- Implement Anthropic cloud execution.
- Implement Ollama local execution.
- Add provider configuration/toggle.
- Validate the same workflows on both providers.

### Phase 6 — Frontend

- Build chat interface.
- Add session controls.
- Add provider/model indicator.
- Add citations.
- Build Artifact Viewer.
- Add responsive and failure states.

### Phase 7 — Observability & resilience

- Configure LangSmith.
- Add structured logs.
- Add dependency health checks.
- Add graceful failure handling.

### Phase 8 — Testing & evaluation

- Add API tests.
- Add persistence tests.
- Add retrieval tests.
- Add routing tests.
- Add session-isolation tests.
- Add artifact security tests.
- Add Ship 30 validation tests.
- Build a small 15–20 question RAG benchmark.
- Run manual UI tests.

### Phase 9 — Finalization

- Verify clean setup from documented instructions.
- Verify no secrets are committed.
- Align documentation with actual implementation.
- Validate the Ollama demo path.
- Validate cloud path.
- Record the final demonstration.

## 21. Definition of Done

The product is considered complete when:

1. A fresh evaluator can configure the documented environment and run the application through a reproducible workflow.
2. The application answers supported product/growth questions using Lenny transcript evidence.
3. Sources are clearly identified for grounded answers.
4. Unsupported questions are handled without hallucinated certainty.
5. Sessions maintain independent context.
6. Anthropic Claude works through the Claude Agent SDK.
7. Ollama works for the required local demo.
8. The three required skills work independently.
9. Ship 30 output is validated and can self-correct once.
10. Markdown and HTML/CSS artifacts render inside the application.
11. Generated HTML is treated as untrusted and safely isolated/sanitized.
12. LangSmith provides useful AI execution traces.
13. Operational failures are visible through structured logs and actionable errors.
14. Critical automated tests pass.
15. The RAG benchmark demonstrates the target grounding quality.
16. The implementation remains within the defined scope.
17. The final system can be understood and extended by another engineer.

## Final Technical Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React + Vite + Tailwind/shadcn | Conversational UI and Artifact Viewer |
| Backend | FastAPI + Python | API, orchestration boundary and application services |
| Agent runtime | Anthropic Claude Agent SDK | Agent execution and skill routing |
| Cloud LLM | Anthropic Claude | High-quality cloud generation |
| Local LLM | Ollama | Required local model execution |
| Embeddings | BAAI/bge-small-en-v1.5 | Local transcript/query embeddings |
| Database | Supabase PostgreSQL | Persistent application and knowledge data |
| Vector search | pgvector | Semantic retrieval |
| Keyword search | PostgreSQL full-text search | Exact/lexical retrieval |
| RAG | Hybrid + corrective retrieval + grounding validation | Reliable knowledge retrieval |
| Agent skills | Grounded QA / Ship 30 / Artifact Generation | Clear agent responsibilities |
| Observability | LangSmith + structured logs | AI tracing and operational diagnostics |
| Artifact security | Sanitization + sandboxed/isolation rendering | Safe generated HTML |
| Testing | Automated tests + RAG benchmark + manual UI plan | Reliability and evaluation |
| Deployment | Docker Compose / reproducible workflow | Local setup and handoff |

## Implementation status addendum

This PRD remains the target specification; the status below distinguishes implementation from live-environment verification. The current codebase includes the selected indexed transcript corpus, local BGE embeddings, PostgreSQL/pgvector retrieval, a separate hybrid/corrective retrieval service, Claude Agent SDK and Ollama provider paths, the three tool/workflow capabilities, PostgreSQL-backed conversation sessions with a 24-hour in-memory execution-context optimization, SSE generation streaming, the React frontend, Docker files, and optional LangSmith tracing.

The following items require explicit target-environment verification or follow-up: live database/session restart behavior, authenticated session ownership, artifact HTML sanitization/isolation verification, the 15–20 question benchmark and measured grounding rate, live LangSmith trace inspection, Docker Compose execution, and any submission screenshots beyond the supplied `architecture.png`. The active agent tool is wired to the semantic `Retriever`; hybrid/corrective retrieval exists as a separate service and should be benchmarked and wired into the production path only after that evaluation. See `README.md`, `architecture.md`, `manual-testing.md`, `security.md`, and `SUBMISSION_CHECKLIST.md` for the current boundaries.
