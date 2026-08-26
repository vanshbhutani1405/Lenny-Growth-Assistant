# Session persistence summary

Conversation support progressed from live in-memory context to PostgreSQL-backed persistence. Current models are `ConversationSession` and `ConversationMessage`, created by Alembic revision `0003_conversation_sessions`. `SessionManager` creates, loads, lists, continues, and deletes sessions; it persists successful user/assistant turns, reconstructs bounded history, keeps a 24-hour in-memory provider-context optimization, and removes expired live state without deleting durable rows. Live restart behavior still needs target-database verification.
