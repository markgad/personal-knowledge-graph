# Hybrid search for RAG

Hybrid search combines keyword search (like BM25) with semantic vector
search. Keyword search is precise for exact terms, acronyms, and names.
Semantic search is better at matching meaning and paraphrase.

## Reciprocal rank fusion

A simple, robust way to combine two ranked lists without needing to
normalize scores onto the same scale is reciprocal rank fusion (RRF).
Each item gets a score of 1 / (k + rank) from each list, and the scores
are summed across lists.
