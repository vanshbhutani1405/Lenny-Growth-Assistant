# Agent, tools, and workflow summary

The agent layer retained Claude Agent SDK support and added a provider-neutral Ollama path. A central registry exposes `search_transcripts`, `validate_ship30_draft`, and `create_artifact`. Workflow routing covers `grounded_qa`, `research_synthesis`, and `ship30`; Ship 30 validation allows one controlled redraft. The same retrieval and source metadata boundaries are used across providers.
