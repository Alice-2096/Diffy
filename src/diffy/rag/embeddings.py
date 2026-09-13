from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class Embedder(Protocol):
    def encode(self, texts: Sequence[str]) -> list[list[float]]: ...

    def encode_query(self, query: str) -> list[float]: ...


class BGEEmbedder:
    """CPU embeddings; model files may be downloaded, document text stays local."""

    model_name = "BAAI/bge-small-en-v1.5"
    dimension = 384
    query_prefix = "Represent this sentence for searching relevant passages: "

    def __init__(self, *, cache_folder: str | None = None, offline: bool = False):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Install RAG dependencies: pip install -e '.[rag]'"
            ) from exc
        self._model = SentenceTransformer(
            self.model_name,
            device="cpu",
            cache_folder=cache_folder,
            local_files_only=offline,
            trust_remote_code=False,
        )

    def _fits(self, text: str) -> bool:
        tokens = self._model.tokenizer(
            text,
            truncation=False,
            verbose=False,
        )["input_ids"]
        return len(tokens) <= self._model.max_seq_length

    def split_text(self, text: str) -> list[str]:
        """Split oversized sections, retaining original text without truncation."""
        if not text.strip():
            return []
        if self._fits(text):
            return [text]
        midpoint = len(text) // 2
        cut = text.rfind(" ", 0, midpoint + 1)
        if cut <= 0:
            cut = midpoint
        if cut == 0:
            raise ValueError("Text cannot fit the embedding model token limit")
        return self.split_text(text[:cut]) + self.split_text(text[cut:])

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        if any(not text.strip() or not self._fits(text) for text in texts):
            raise ValueError(
                "Embedding input is blank or exceeds the model token limit"
            )
        return self._model.encode(
            list(texts),
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        ).tolist()

    def encode_query(self, query: str) -> list[float]:
        if not query.strip():
            raise ValueError("Query must not be blank")
        return self.encode([self.query_prefix + query])[0]
