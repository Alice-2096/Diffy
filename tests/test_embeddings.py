import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from diffy.rag.embeddings import BGEEmbedder


@pytest.fixture
def adapter(monkeypatch):
    model = Mock()
    model.max_seq_length = 80
    model.tokenizer.side_effect = lambda text, **kwargs: {"input_ids": list(text)}
    model.encode.return_value.tolist.return_value = [[1.0, 0.0]]
    constructor = Mock(return_value=model)
    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(SentenceTransformer=constructor),
    )
    embedder = BGEEmbedder(cache_folder="cache", offline=True)
    return embedder, model, constructor


def test_local_model_options_and_query_prefix(adapter):
    embedder, model, constructor = adapter
    constructor.assert_called_once_with(
        "BAAI/bge-small-en-v1.5",
        device="cpu",
        cache_folder="cache",
        local_files_only=True,
        trust_remote_code=False,
    )
    embedder.encode(["network"])
    assert model.encode.call_args.args[0] == ["network"]
    assert model.encode.call_args.kwargs["normalize_embeddings"] is True
    embedder.encode_query("network")
    assert model.encode.call_args.args[0] == [BGEEmbedder.query_prefix + "network"]


def test_long_sections_are_preserved_without_truncation(adapter):
    embedder, _, _ = adapter
    for text in ("network policy " * 100, "x" * 300):
        parts = embedder.split_text(text)
        assert "".join(parts) == text
        assert all(len(part) <= 80 for part in parts)
    assert embedder.split_text(" ") == []
    assert embedder.encode([]) == []
    with pytest.raises(ValueError, match="token limit"):
        embedder.encode(["x" * 81])
    with pytest.raises(ValueError):
        embedder.encode_query(" ")
