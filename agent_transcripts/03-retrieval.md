# Retrieval summary

The semantic retriever was built on the existing PostgreSQL/pgvector data and exposes top-k, minimum-score, episode, guest, and source metadata behavior. A separate retrieval service contains keyword/semantic merging and one corrective attempt. The active transcript-search tool is wired to the focused semantic `Retriever`; benchmark results and full hybrid-path integration remain explicit verification work.
