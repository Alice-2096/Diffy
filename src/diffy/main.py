from __future__ import annotations

import argparse
import json
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
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command != "analyze":
        raise SystemExit(2)

    findings = DiffAnalyzer().analyze(args.diff.read_text(encoding="utf-8"))
    rendered = json.dumps(
        {"findings": [finding.to_dict() for finding in findings]},
        indent=2,
    )

    if args.output:
        args.output.write_text(f"{rendered}\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
