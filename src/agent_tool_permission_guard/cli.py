"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import PolicyError, evaluate_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate an AI agent tool-call plan")
    parser.add_argument("plan", type=Path, help="JSON policy and proposed tool calls")
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        document = json.loads(args.plan.read_text(encoding="utf-8"))
        result = evaluate_plan(document)
    except (OSError, json.JSONDecodeError, PolicyError) as exc:
        print(json.dumps({"decision": "BLOCK", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, indent=None if args.compact else 2, sort_keys=True))
    return 0 if result["decision"] == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())

