"""
Hybrid search = BM25 keyword search (SQLite FTS5) + vector cosine search
(sqlite-vec), combined with Reciprocal Rank Fusion (RRF).

RRF instead of a weighted score blend because BM25 scores and cosine
distances live on completely different, uncalibrated scales -- fusing by
*rank* rather than raw score avoids having to hand-tune a weight that
would silently break as soon as the corpus size or embedding model
changes. It's also just two lines of code and is a well-established
baseline for hybrid search.
"""
from __future__ import annotations

import re
import sqlite3

import sqlite_vec

from app.config import settings
from app.db import get_connection
from app.embeddings import get_embedding_provider

_WORD_RE = re.compile(r"[A-Za-z0-9_]+")


def _sanitize_fts_query(q: str) -> str:
    """Turn free-text user input into a safe, OR-of-terms FTS5 MATCH query."""
    terms = _WORD_RE.findall(q)
    if not terms:
        return ""
    return " OR ".join(f'"{t}"' for t in terms)


def _keyword_ranked_ids(conn: sqlite3.Connection, query: str, limit: int) -> list[int]:
    fts_query = _sanitize_fts_query(query)
    if not fts_query:
        return []
    rows = conn.execute(
        "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts) LIMIT ?",
        (fts_query, limit),
    ).fetchall()
    return [r["rowid"] for r in rows]


def _semantic_ranked_ids(conn: sqlite3.Connection, query: str, limit: int) -> list[int]:
    provider = get_embedding_provider()
    vec = provider.embed_one(query)
    rows = conn.execute(
        "SELECT rowid FROM vec_chunks WHERE embedding MATCH ? AND k = ? ORDER BY distance",
        (sqlite_vec.serialize_float32(vec), limit),
    ).fetchall()
    return [r["rowid"] for r in rows]


def _reciprocal_rank_fusion(ranked_lists: list[list[int]], k: int) -> dict[int, float]:
    scores: dict[int, float] = {}
    for ranked_ids in ranked_lists:
        for rank, chunk_id in enumerate(ranked_ids, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return scores


def _make_snippet(text: str, query: str, radius: int = 160) -> str:
    terms = _WORD_RE.findall(query.lower())
    lower = text.lower()
    pos = -1
    for t in terms:
        pos = lower.find(t)
        if pos != -1:
            break
    if pos == -1:
        snippet = text[: radius * 2]
    else:
        start = max(0, pos - radius)
        end = min(len(text), pos + radius)
        snippet = text[start:end]
    snippet = snippet.strip().replace("\n", " ")
    if len(snippet) < len(text):
        snippet = ("…" if snippet != text[:len(snippet)] else "") + snippet + "…"
    return snippet


def hybrid_search(query: str, top_k: int | None = None) -> list[dict]:
    top_k = top_k or settings.default_top_k
    candidate_pool = max(top_k * 4, 20)  # pull a wider pool before fusing/truncating

    conn = get_connection()
    try:
        keyword_ids = _keyword_ranked_ids(conn, query, candidate_pool)
        semantic_ids = _semantic_ranked_ids(conn, query, candidate_pool)
        fused = _reciprocal_rank_fusion([keyword_ids, semantic_ids], k=settings.rrf_k)

        if not fused:
            return []

        top_ids = sorted(fused.keys(), key=lambda cid: fused[cid], reverse=True)[:top_k]

        results = []
        for chunk_id in top_ids:
            row = conn.execute(
                """
                SELECT chunks.id as chunk_id, chunks.text, chunks.start_line, chunks.end_line,
                       notes.id as note_id, notes.title, notes.path
                FROM chunks JOIN notes ON notes.id = chunks.note_id
                WHERE chunks.id = ?
                """,
                (chunk_id,),
            ).fetchone()
            if row is None:
                continue
            results.append(
                {
                    "chunk_id": row["chunk_id"],
                    "note_id": row["note_id"],
                    "title": row["title"],
                    "path": row["path"],
                    "start_line": row["start_line"],
                    "end_line": row["end_line"],
                    "snippet": _make_snippet(row["text"], query),
                    "score": round(fused[chunk_id], 5),
                    "matched_keyword": chunk_id in keyword_ids,
                    "matched_semantic": chunk_id in semantic_ids,
                }
            )
        return results
    finally:
        conn.close()
