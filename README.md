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
