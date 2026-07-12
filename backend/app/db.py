"""
SQLite is the entire storage layer: regular tables for notes/chunks,
an FTS5 virtual table for keyword (BM25) search, and a sqlite-vec
virtual table for vector (cosine) search. One file, no extra services --
that's the "local-first" part of the pitch.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import sqlite_vec

from app.config import settings
from app.embeddings import get_embedding_provider


def _connect_raw() -> sqlite3.Connection:
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def get_connection() -> sqlite3.Connection:
    return _connect_raw()


def init_db() -> None:
    """Create tables if they don't exist yet. Safe to call on every startup."""
    dim = get_embedding_provider().dim
    conn = _connect_raw()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                path    TEXT UNIQUE NOT NULL,
                title   TEXT NOT NULL,
                mtime   REAL NOT NULL,
                content TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id     INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                text        TEXT NOT NULL,
                start_line  INTEGER NOT NULL,
                end_line    INTEGER NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                text,
                content=''
            );
            """
        )
        # vec0 tables can't be created with "IF NOT EXISTS" reliably across
        # versions, and the vector dimension is baked in at creation time
        # (it depends on which embedding model is configured), so guard
        # manually.
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE name='vec_chunks'"
        ).fetchone()
        if not exists:
            conn.execute(
                f"CREATE VIRTUAL TABLE vec_chunks USING vec0(embedding float[{dim}])"
            )
        conn.commit()
    finally:
        conn.close()


def reset_note_chunks(conn: sqlite3.Connection, note_id: int) -> None:
    """Delete existing chunks (+ fts + vec rows) for a note before re-ingesting it."""
    rows = conn.execute("SELECT id FROM chunks WHERE note_id = ?", (note_id,)).fetchall()
    ids = [r["id"] for r in rows]
    for cid in ids:
        conn.execute("DELETE FROM chunks_fts WHERE rowid = ?", (cid,))
        conn.execute("DELETE FROM vec_chunks WHERE rowid = ?", (cid,))
    conn.execute("DELETE FROM chunks WHERE note_id = ?", (note_id,))


def insert_chunk(
    conn: sqlite3.Connection,
    note_id: int,
    chunk_index: int,
    text: str,
    start_line: int,
    end_line: int,
    embedding: list[float],
) -> int:
    cur = conn.execute(
        "INSERT INTO chunks (note_id, chunk_index, text, start_line, end_line) "
        "VALUES (?, ?, ?, ?, ?)",
        (note_id, chunk_index, text, start_line, end_line),
    )
    chunk_id = cur.lastrowid
    conn.execute(
        "INSERT INTO chunks_fts (rowid, text) VALUES (?, ?)", (chunk_id, text)
    )
    conn.execute(
        "INSERT INTO vec_chunks (rowid, embedding) VALUES (?, ?)",
        (chunk_id, sqlite_vec.serialize_float32(embedding)),
    )
    return chunk_id
