from dataclasses import replace

import pytest

from diffy.rag.ingest import ingest_markdown
from diffy.rag.models import KnowledgeChunk
from diffy.rag.retrieve import LocalRetriever
from diffy.rag.store import QdrantLocalStore

pytest.importorskip("qdrant_client")


class TinyEmbedder:
    def encode(self, texts):
        return [[1.0, 0.0] if "network" in text else [0.0, 1.0] for text in texts]

    def encode_query(self, query):
        return self.encode([query])[0]


def chunk(id="a", source_type="policy"):
    return KnowledgeChunk(
        id,
        "network policy",
        "policy.md",
        source_type,
        "example",
        section="Network",
        metadata={"version": "1"},
    )


def test_persistence_filtering_and_idempotent_upsert(tmp_path):
    policy = chunk()
    example = replace(chunk("b", "history"), source="pr/1")
    with QdrantLocalStore(tmp_path, dimension=2) as store:
        store.upsert([policy, example], [[1, 0], [1, 0]])
        store.upsert([policy], [[1, 0]])
    with QdrantLocalStore(tmp_path, dimension=2) as store:
        retriever = LocalRetriever(TinyEmbedder(), store)
        assert retriever.search("network", source_types=("policy",)) == [policy]
        assert retriever.search("network", source_types=("history",)) == [example]
        assert retriever.search("network", source_types=()) == []
        assert (
            len(
                retriever.search("network", source_types=("policy", "history"), limit=1)
            )
            == 1
        )


def test_ingest_refresh_removes_stale_chunks_and_empty_document(tmp_path):
    document = tmp_path / "policy.md"
    document.write_text("# Network\nnetwork rule\n# IAM\nIAM rule")
    with QdrantLocalStore(tmp_path / "db", dimension=2) as store:

        def ingest():
            return ingest_markdown(
                document,
                source_type="policy",
                authority="example",
                embedder=TinyEmbedder(),
                store=store,
                split_text=lambda text: [text],
            )

        assert ingest() == 2
        document.write_text("# Network\nnetwork updated")
        assert ingest() == 1
        found = store.search([1, 0], source_types=("policy",), limit=10)
        assert [item.text for item in found] == ["network updated"]
        assert found[0].section == "Network"
        assert found[0].source == str(document)
        document.write_text("")
        assert ingest() == 0
        assert store.search([1, 0], source_types=("policy",)) == []


@pytest.mark.parametrize("vectors", [[], [[1]], [[float("nan"), 1]], [[0, 0]]])
def test_invalid_vectors_do_not_remove_existing_evidence(tmp_path, vectors):
    with QdrantLocalStore(tmp_path, dimension=2) as store:
        store.upsert([chunk()], [[1, 0]])
        with pytest.raises(ValueError):
            store.replace_source("policy.md", [chunk()], vectors)
        assert store.search([1, 0], source_types=("policy",)) == [chunk()]


def test_incompatible_collection_fails_and_releases_lock(tmp_path):
    with QdrantLocalStore(tmp_path, dimension=2):
        pass
    with pytest.raises(ValueError, match="incompatible"):
        QdrantLocalStore(tmp_path, dimension=3)
    with QdrantLocalStore(tmp_path, dimension=2):
        pass


def test_retriever_validates_before_embedding():
    retriever = LocalRetriever(None, None)
    with pytest.raises(ValueError):
        retriever.search(" ", source_types=("policy",))
    with pytest.raises(ValueError):
        retriever.search("network", source_types=("policy",), limit=0)
    assert retriever.search("network", source_types=()) == []
