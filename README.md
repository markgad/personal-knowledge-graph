# Personal Knowledge Graph — v1 (notes search)

v1 scope only: ingest a folder of markdown notes, chunk + embed them, and
search them with hybrid keyword + semantic search through a minimal web UI.
No graph, no entity extraction, no PDFs/bookmarks, no chat/RAG Q&A yet —
see [Roadmap](#roadmap).

## Architecture

```
┌─────────────┐   fetch /api/*   ┌──────────────┐        ┌──────────────────┐
│  React UI    │ ───────────────▶ │  FastAPI      │ ──────▶ │  SQLite (1 file)  │
│  (Vite)      │ ◀─────────────── │  backend      │ ◀────── │  + sqlite-vec     │
└─────────────┘                  └──────┬───────┘        │  + FTS5           │
                                          │                └──────────────────┘
                                          ▼
                                 sentence-transformers
                                 (or OpenAI embeddings)
```

- **Storage**: a single SQLite file holds everything — notes, chunks, an
  FTS5 virtual table for BM25 keyword search, and a `sqlite-vec` `vec0`
  virtual table for vector search. No separate vector DB server to run.
- **Chunking**: markdown is split into paragraphs, then greedily packed
  into ~1000-character chunks with a small overlap, each chunk keeping
  the source file's line numbers for citations.
- **Search**: keyword (BM25) and semantic (cosine) results are combined
  with **Reciprocal Rank Fusion** — see `backend/app/search.py` for why
  RRF instead of a weighted score blend.

### Embeddings: local vs. OpenAI

The app supports both, switched via `PKG_EMBEDDING_PROVIDER`:

| | `local` (default) | `openai` |
|---|---|---|
| Model | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) | `text-embedding-3-small` (1536-dim) |
| Cost | Free | ~$0.02 per 1M tokens |
| Privacy | Nothing leaves your machine | Note text sent to OpenAI's API |
| Quality | Good baseline, especially for short/technical notes | Noticeably better on longer or more abstract text |
| Requirements | ~90MB model download once, then fully offline | Internet + API key, always |
| Speed | Fine on CPU for a personal note collection; slower without a GPU at large scale | Network latency per request, but no local compute |

Default is `local` because the project's whole premise is local-first;
`openai` is there for when you want better recall and are fine with the
tradeoff. Switching providers requires re-ingesting (the vector table's
dimensionality is fixed to whichever model created it).

## Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # edit PKG_NOTES_DIR at minimum
uvicorn app.main:app --reload --port 8000
```

First run of the `local` embedding provider downloads the model from
Hugging Face (~90MB) — you need internet for that one time, then it's
cached and works offline.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api/*` to
`http://localhost:8000`, so both need to be running.

### Try it

1. In the UI, type a folder path (or leave blank to use `PKG_NOTES_DIR`)
   and click **run ingest**. There's a couple of sample notes in
   `sample_notes/` you can point at to try it immediately.
2. Search for a word, phrase, or idea. Semantic matches show up even
   when the exact words aren't in the note.
3. Click a result's title to expand the full note inline.

Re-running ingest on the same folder only re-embeds files that changed
(tracked by mtime), so it's cheap to re-run after editing notes.

## API

- `POST /api/ingest {folder_path?}` — scan and (re)index markdown files
- `GET /api/search?q=...&top_k=10` — hybrid search
- `GET /api/notes` — list indexed notes
- `GET /api/notes/{id}` — full note content

## Roadmap (explicitly out of scope for v1)

- Graph visualization
- Entity extraction / auto-linking between notes
- PDF and bookmark ingestion
- Chat / RAG question-answering interface
- Resurfacing / spaced repetition
