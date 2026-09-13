from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from diffy.analyzers.diff import DiffAnalyzer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="diffy",
        description="Review infrastructure changes before invoking an LLM.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="analyze a unified diff")
    analyze.add_argument("--diff", type=Path, required=True, help="diff file")
    analyze.add_argument("--output", type=Path, help="write JSON to this file")
    ingest = subparsers.add_parser("ingest", help="index local Markdown knowledge")
    ingest.add_argument("path", type=Path)
    ingest.add_argument("--source-type", required=True)
    ingest.add_argument("--authority", required=True)
    search = subparsers.add_parser("search", help="retrieve local knowledge")
    search.add_argument("query")
    search.add_argument("--source-type", action="append", required=True)
    search.add_argument("--limit", type=int, default=5)
    for command in (ingest, search):
        command.add_argument("--db", type=Path, default=Path(".data/qdrant"))
        command.add_argument("--model-cache", type=Path, default=Path(".data/models"))
        command.add_argument(
            "--offline",
            action="store_true",
            help="use cached model files without downloading",
        )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command != "analyze":
        try:
            result = run_rag(args)
        except (OSError, ValueError, RuntimeError) as exc:
            parser.exit(1, f"diffy: {exc}\n")
        print(json.dumps(result, indent=2))
        return

    findings = DiffAnalyzer().analyze(args.diff.read_text(encoding="utf-8"))
    rendered = json.dumps(
        {"findings": [finding.to_dict() for finding in findings]},
        indent=2,
    )

    if args.output:
        args.output.write_text(f"{rendered}\n", encoding="utf-8")
    else:
        print(rendered)


def run_rag(args: argparse.Namespace) -> dict:
    # Keep optional ML dependencies out of the deterministic analyze path.
    from diffy.rag.embeddings import BGEEmbedder
    from diffy.rag.ingest import ingest_markdown
    from diffy.rag.retrieve import LocalRetriever
    from diffy.rag.store import QdrantLocalStore

    if args.command == "search" and (not args.query.strip() or args.limit < 1):
        raise ValueError("Query must not be blank and limit must be positive")
    if args.command == "ingest":
        args.path.resolve(strict=True)
        if not args.source_type.strip() or not args.authority.strip():
            raise ValueError("Source type and authority must not be blank")
    embedder = BGEEmbedder(cache_folder=str(args.model_cache), offline=args.offline)
    with QdrantLocalStore(args.db, dimension=embedder.dimension) as store:
        if args.command == "ingest":
            count = ingest_markdown(
                args.path,
                source_type=args.source_type,
                authority=args.authority,
                embedder=embedder,
                store=store,
                split_text=embedder.split_text,
            )
            return {"indexed_chunks": count}
        chunks = LocalRetriever(embedder, store).search(
            args.query,
            source_types=tuple(args.source_type),
            limit=args.limit,
        )
        return {"chunks": [asdict(chunk) for chunk in chunks]}


if __name__ == "__main__":
    main()
