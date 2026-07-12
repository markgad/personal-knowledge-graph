from fastapi import APIRouter, HTTPException, Query

from app.db import get_connection
from app.search import hybrid_search

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search")
def search(q: str = Query(..., min_length=1), top_k: int = Query(10, ge=1, le=50)):
    results = hybrid_search(q, top_k=top_k)
    return {"query": q, "results": results}


@router.get("/notes/{note_id}")
def get_note(note_id: int):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, path, title, mtime, content FROM notes WHERE id = ?", (note_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Note not found")
        return dict(row)
    finally:
        conn.close()


@router.get("/notes")
def list_notes():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, path, title, mtime FROM notes ORDER BY title"
        ).fetchall()
        return {"notes": [dict(r) for r in rows]}
    finally:
        conn.close()
