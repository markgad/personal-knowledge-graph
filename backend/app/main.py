from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routers import ingest, search

app = FastAPI(title="Personal Knowledge Graph — v1 (notes search)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local-first single-user app; tighten if you expose it
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(search.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}
