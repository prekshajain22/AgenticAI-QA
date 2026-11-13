"""Agents CLI.

Goal
----
Run prompt-defined agents from the command line by loading Markdown specs from
``agents/specs/*.md``.

Usage
-----
List available agent specs:
    python -m agents.cli list

Render the final system prompt (after variable substitution):
    python -m agents.cli render jira_bug_analyst --var project_key=CRED 
    --var project_name=CreditCardBanking

Note: The full 'run' (LLM execution) command will be added next once we agree on
the desired model client / MCP wiring for CLI execution.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from agents.agent_specs import AgentSpecLoader


def _parse_vars(pairs: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for raw in pairs or []:
        if "=" not in raw:
            raise SystemExit(f"--var must be key=value, got: {raw}")
        k, v = raw.split("=", 1)
        result[k] = v
    return result


def cmd_list(args: argparse.Namespace) -> int:
    loader = AgentSpecLoader()
    for spec_id in loader.list_ids():
        print(spec_id)
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    loader = AgentSpecLoader()
    spec = loader.load_by_id(args.spec_id)
    variables = _parse_vars(args.var)
    rendered = spec.render(**variables)
    if args.json:
        print(json.dumps({"id": spec.id, "name": spec.name, "system_message": rendered}, indent=2))
    else:
        print(rendered)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agents", description="Agent spec CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List available agent spec ids")
    p_list.set_defaults(func=cmd_list)

    p_render = sub.add_parser("render", help="Render a spec to a final system prompt")
    p_render.add_argument("spec_id", help="Spec id (filename without .md)")
    p_render.add_argument(
        "--var",
        action="append",
        default=[],
        help="Template variable substitution in the form key=value (repeatable).",
    )
    p_render.add_argument("--json", action="store_true", help="Output JSON wrapper")
    p_render.set_defaults(func=cmd_render)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
