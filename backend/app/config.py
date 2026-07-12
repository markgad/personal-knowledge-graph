"""
Central configuration. Everything is overridable via environment variables
(or a .env file in backend/), so v1 stays a single source of truth for
paths and model choice.
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="PKG_", extra="ignore")

    # Folder that gets watched/ingested for markdown notes.
    notes_dir: str = str(Path.home() / "notes")

    # Where the SQLite database (data + vectors) lives.
    db_path: str = str(Path(__file__).resolve().parent.parent / "data" / "pkg.db")

    # "local" (sentence-transformers, runs on your machine, free, private)
    # or "openai" (higher quality embeddings, costs money, sends text to OpenAI).
    embedding_provider: str = "local"

    # Used when embedding_provider == "local".
    local_embedding_model: str = "all-MiniLM-L6-v2"   # 384 dims, fast, good baseline
    # Used when embedding_provider == "openai".
    openai_embedding_model: str = "text-embedding-3-small"  # 1536 dims
    openai_api_key: str | None = None

    # Chunking.
    chunk_size_chars: int = 1000
    chunk_overlap_chars: int = 150

    # Hybrid search tuning.
    default_top_k: int = 10
    rrf_k: int = 60  # reciprocal-rank-fusion constant (60 is the standard default)


settings = Settings()
