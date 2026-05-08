# AGENTS.md

Failure-memory module for minimal-shot VLA context.

- Store abstract safety principles, not verbose chain-of-thought.
- Keep retrieval deterministic and dependency-free in the local harness.
- Do not encode benchmark-specific route answers as if they were general rules.
- Label the current retrieval substrate honestly as lexical/tag-overlap RAG; do
  not claim embeddings, vector search, or semantic RAG until an actual index is
  built and evidenced. See `MEM-0043`.
