from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .flask_indexer import FlaskRouteIndexer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aahar-tester",
        description="Index backend repos and prepare them for test generation.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser(
        "index",
        help="Build a static route index for a target repository.",
    )
    index_parser.add_argument("target", help="Path to the repository to inspect.")
    index_parser.add_argument(
        "--framework",
        choices=["flask"],
        default="flask",
        help="Backend framework adapter to use.",
    )
    index_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "index":
        index = build_index(Path(args.target), framework=args.framework)
        print(json.dumps(index.to_dict(), indent=2 if args.pretty else None))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def build_index(target: Path, framework: str):
    if framework != "flask":
        raise ValueError(f"Unsupported framework: {framework}")
    return FlaskRouteIndexer(target).build_index()

