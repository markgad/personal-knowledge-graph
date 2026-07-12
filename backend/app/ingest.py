from __future__ import annotations

import os
from pathlib import Path

import frontmatter

from app.chunking import chunk_markdown
from app.config import settings
from app.db import get_connection, insert_chunk, reset_note_chunks
from app.embeddings import get_embedding_provider


def _extract_title(post: frontmatter.Post, path: Path) -> str:
    if post.get("title"):
        return str(post["title"])
    for line in post.content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return path.stem


def ingest_folder(folder_path: str | None = None) -> dict:
    folder = Path(folder_path or settings.notes_dir).expanduser().resolve()
    if not folder.exists():
        raise FileNotFoundError(f"Notes folder does not exist: {folder}")

    md_files = sorted(folder.rglob("*.md"))
    provider = get_embedding_provider()

    conn = get_connection()
    stats = {"scanned": len(md_files), "ingested": 0, "skipped_unchanged": 0, "chunks": 0}
    try:
        for path in md_files:
            mtime = path.stat().st_mtime
            existing = conn.execute(
                "SELECT id, mtime FROM notes WHERE path = ?", (str(path),)
            ).fetchone()

            if existing and existing["mtime"] == mtime:
                stats["skipped_unchanged"] += 1
                continue

            raw = path.read_text(encoding="utf-8", errors="replace")
            post = frontmatter.loads(raw)
            title = _extract_title(post, path)
            body = post.content

            if existing:
                note_id = existing["id"]
                conn.execute(
                    "UPDATE notes SET title = ?, mtime = ?, content = ? WHERE id = ?",
                    (title, mtime, body, note_id),
                )
                reset_note_chunks(conn, note_id)
            else:
                cur = conn.execute(
                    "INSERT INTO notes (path, title, mtime, content) VALUES (?, ?, ?, ?)",
                    (str(path), title, mtime, body),
                )
                note_id = cur.lastrowid

            chunks = chunk_markdown(
                body,
                chunk_size=settings.chunk_size_chars,
                overlap=settings.chunk_overlap_chars,
            )
            if chunks:
                embeddings = provider.embed([c.text for c in chunks])
                for idx, (chunk, vec) in enumerate(zip(chunks, embeddings)):
                    insert_chunk(
                        conn, note_id, idx, chunk.text, chunk.start_line, chunk.end_line, vec
                    )
                stats["chunks"] += len(chunks)

            stats["ingested"] += 1
            conn.commit()
    finally:
        conn.close()

    return stats
