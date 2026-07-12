# Personal Knowledge Graph — v1

Search your markdown notes locally. Point it at a folder, it indexes the notes, and you can search them by keyword or by meaning.

No graph view or chat interface yet — just search for now.

## Run it

**Backend** (Terminal 1):

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Before running uvicorn, open `.env` and set `PKG_NOTES_DIR` to your notes folder.

**Frontend** (Terminal 2):

```powershell
cd frontend
npm install
npm run dev
```

Open the link it gives you (usually `http://localhost:5173`).

## Using it

1. Type a folder path in "index a folder" and click run ingest (or use `sample_notes/` to test it first)
2. Search for anything
3. Click a result to see the full note


## Later (not built yet)

Graph view, auto-linking notes, PDF/bookmark support, chat Q&A, spaced repetition.
