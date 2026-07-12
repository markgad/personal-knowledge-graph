"""
Embedding provider abstraction.

Two options, picked via PKG_EMBEDDING_PROVIDER:

- "local"  -> sentence-transformers, runs on your own CPU/GPU.
              Free, fully private (nothing leaves your machine), no network
              dependency, works offline. Quality is good-not-great for a
              small model (all-MiniLM-L6-v2, 384 dims) but is the right
              default for a "local-first" app. Slower on large corpora if
              you don't have a GPU, and first run downloads ~90MB of
              model weights from Hugging Face.

- "openai" -> OpenAI's text-embedding-3-small/-large via API.
              Noticeably better retrieval quality, especially on longer
              or more abstract text, and no local compute cost. Downsides:
              requires an API key + internet, costs money per token,
              and your note content is sent to OpenAI's servers -- a
              real tradeoff for a tool whose whole pitch is "local-first".

Both providers implement the same interface so the rest of the app
(ingest, search) never has to know which one is active.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache

from app.config import settings


class EmbeddingProvider(ABC):
    dim: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts, returns one vector per text."""

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


class LocalEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str):
        # Imported lazily so the "openai" path doesn't pay the (heavy)
        # sentence-transformers/torch import cost.
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,  # cosine similarity via dot product
        )
        return vectors.tolist()


class OpenAIEmbeddingProvider(EmbeddingProvider):
    # dims for OpenAI's current embedding models
    _DIMS = {"text-embedding-3-small": 1536, "text-embedding-3-large": 3072}

    def __init__(self, model_name: str, api_key: str | None):
        from openai import OpenAI

        if not api_key:
            raise RuntimeError(
                "PKG_EMBEDDING_PROVIDER=openai requires PKG_OPENAI_API_KEY to be set."
            )
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.dim = self._DIMS.get(model_name, 1536)

    def embed(self, texts: list[str]) -> list[list[float]]:
        # OpenAI's embeddings endpoint accepts a batch of inputs directly.
        resp = self.client.embeddings.create(model=self.model_name, input=texts)
        return [d.embedding for d in resp.data]


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_provider == "local":
        return LocalEmbeddingProvider(settings.local_embedding_model)
    elif settings.embedding_provider == "openai":
        return OpenAIEmbeddingProvider(settings.openai_embedding_model, settings.openai_api_key)
    else:
        raise ValueError(f"Unknown embedding_provider: {settings.embedding_provider!r}")
