# Diffy

Diffy is a compliance-conscious, RAG-assisted reviewer for Terraform,
Kubernetes, Helm, and other infrastructure changes. The project starts with a
small deterministic analyzer and keeps GitHub, retrieval, and LLM integrations
behind replaceable interfaces.

## Design goals

- Detect obvious infrastructure risks deterministically before invoking an LLM.
- Retrieve only relevant policy and historical examples.
- Keep embeddings and vector search local for the POC.
- Treat pull requests, source code, and retrieved text as untrusted input.
- Require structured review output and human review before enforcement.

## Architecture

```text
PR diff -> deterministic analyzers -> retrieval queries -> policy/examples
                                                       -> approved LLM
                                                       -> review report
```

## Repository layout

```text
.github/workflows/   CI and pull-request analysis
knowledge/           Sample policy corpus; replace with approved documents
src/diffy/           Application package
  analyzers/         Deterministic IaC checks
  github/            GitHub API boundary
  rag/               Chunking, embeddings, storage, and retrieval boundaries
  llm/               Approved model endpoint boundary
  review/            Review models and orchestration
tests/                Fast unit tests
```

## Quick start

Requires Python 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
diffy analyze --diff path/to/change.diff
pytest
```

The first implementation detects public ingress, wildcard IAM permissions,
Terraform destroys, and Terraform replacements from a unified diff. It emits
JSON that can later feed retrieval and an approved LLM.

## Planned POC stack

- GitHub REST API via `httpx`
- Structured validation via `pydantic`
- Local embeddings via `sentence-transformers` and `BAAI/bge-small-en-v1.5`
- Local vector search via `qdrant-client`
- Optional exact-term retrieval via BM25
- A company-approved, OpenAI-compatible LLM endpoint

Install the integration dependencies only when needed:

```bash
python -m pip install -e '.[github,rag]'
```

## Security posture

The included workflow is read-only and uploads no repository data. Before
enabling LLM calls, pin dependencies and actions according to company policy,
use least-privilege tokens, never use `pull_request_target` to execute PR code,
and send only the relevant diff fragments and retrieved policy snippets to the
approved endpoint.

Files in `knowledge/` are public POC examples, not real company policy.

## Local retrieval, step by step

1. Install the optional local RAG dependencies in your Python 3.12+ environment:

   ```bash
   python -m pip install -e '.[dev,rag]'
   ```

2. Index the fictional network policy:

   ```bash
   diffy ingest knowledge/security/example-network-policy.md \
     --source-type policy --authority example
   ```

   The first run downloads `BAAI/bge-small-en-v1.5` into `.data/models`.
   Sentence Transformers runs on CPU and produces normalized 384-dimensional
   vectors. Markdown sections are split further using the model's tokenizer
   when necessary, so long sections are not silently truncated. Original text,
   section, absolute source path, source type, and authority remain in the payload.

3. Search the local index:

   ```bash
   diffy search 'Can production workloads accept traffic from 0.0.0.0/0?' \
     --source-type policy --offline
   ```

   Search prints JSON evidence chunks. BGE's retrieval instruction is added only
   to queries. Repeat `--source-type` to search multiple types; `--limit` defaults
   to five. Source types are explicit labels, not inferred from document content.
   Similarity ranks relevance; it does not establish policy authority or approval.

4. Edit a document and repeat the ingest command to refresh it. Its old chunks
   are replaced, including obsolete sections. An empty document clears its
   indexed chunks. A directory argument recursively ingests `.md` files with the
   same supplied metadata; ingest different authority/source groups separately.

Qdrant runs in-process with persistent data in `.data/qdrant`; no server,
Docker, API key, or LLM endpoint is required. `--db` and `--model-cache` override
the local directories. Only one process may open a database directory at a time.
Both defaults are already covered by `.gitignore`. Stored text is plaintext on
disk, so use a directory protected by your normal filesystem access controls.

After caching the model, pass `--offline` to ingest and search to disable model
downloads. For an offline host, copy a populated model cache onto the host first.
Embedding and vector search run locally; the initial model fetch uses Hugging
Face, and normal online model loading may check for updates. No document text
is sent for inference. No GitHub or LLM calls are introduced by these commands.

This first pipeline refreshes documents individually, not in a corpus-wide
transaction. Deleted or renamed files are not automatically pruned; use a fresh
`--db` directory and ingest the current corpus to rebuild a complete snapshot.
Keep the embedding model fixed for a database. Query inputs beyond its token
limit fail explicitly. Retrieval is not yet wired into the review orchestrator.

Run `ruff check .` and `pytest` after changes. The base test suite works without
RAG dependencies; Qdrant integration tests run when `qdrant-client` is installed.
CI exercises both environments without downloading embedding weights. Embedding
unit tests verify adapter behavior with a stand-in model; real-model relevance
should also be checked locally against your approved corpus.

Implementation references: [BGE model card](https://huggingface.co/BAAI/bge-small-en-v1.5),
[Sentence Transformers](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html),
and [Qdrant Python client](https://github.com/qdrant/qdrant-client).
