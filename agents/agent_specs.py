"""Markdown-based Agent Specs.

This module lets you define agent prompts/specs as Markdown files with YAML
frontmatter, so prompt iteration doesn't require editing Python code.

Convention
----------
- Specs live under ``agents/specs/*.md``
- Each spec has YAML frontmatter including at minimum:

    id: <string>
    name: <string>

- The Markdown body is treated as the system message template and may contain
  Python ``str.format`` placeholders, e.g. ``{project_key}``.

Example
-------
>>> from agents.agent_specs import AgentSpecLoader
>>> spec = AgentSpecLoader().load_by_id("jira_bug_analyst")
>>> msg = spec.render(project_key="CRED", project_name="CreditCardBanking")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import frontmatter


@dataclass(frozen=True)
class AgentSpec:
    id: str
    name: str
    description: str | None = None
    template_vars: list[str] = field(default_factory=list)
    defaults: dict[str, Any] = field(default_factory=dict)
    system_message_template: str = ""

    def render(self, **kwargs: Any) -> str:
        """Render the system message template using ``str.format``."""
        # Optional safety: ensure declared vars exist (when provided)
        missing = [v for v in self.template_vars if v not in kwargs]
        if missing:
            raise ValueError(f"Missing template vars for spec '{self.id}': {missing}")
        try:
            return self.system_message_template.format(**kwargs).strip()
        except KeyError as e:
            raise ValueError(
                f"Missing template var {e!s} for spec '{self.id}'. "
                f"Provided: {sorted(kwargs.keys())}"
            ) from e


class AgentSpecLoader:
    def __init__(self, specs_dir: str | Path | None = None) -> None:
        self._specs_dir = Path(specs_dir) if specs_dir else Path(__file__).parent / "specs"

    @property
    def specs_dir(self) -> Path:
        return self._specs_dir

    def load_from_path(self, path: str | Path) -> AgentSpec:
        p = Path(path)
        post = frontmatter.load(p)

        data = dict(post.metadata or {})
        spec_id = data.get("id") or p.stem
        name = data.get("name") or spec_id

        template_vars = data.get("template_vars") or []
        if not isinstance(template_vars, list):
            raise ValueError(f"template_vars must be a list in {p}")

        defaults = data.get("defaults") or {}
        if not isinstance(defaults, dict):
            raise ValueError(f"defaults must be a mapping in {p}")

        return AgentSpec(
            id=str(spec_id),
            name=str(name),
            description=data.get("description"),
            template_vars=[str(x) for x in template_vars],
            defaults=defaults,
            system_message_template=(post.content or "").strip(),
        )

    def load_by_id(self, spec_id: str) -> AgentSpec:
        path = self.specs_dir / f"{spec_id}.md"
        if not path.exists():
            raise FileNotFoundError(f"No agent spec found at: {path}")
        return self.load_from_path(path)

    def list_ids(self) -> list[str]:
        if not self.specs_dir.exists():
            return []
        return sorted([p.stem for p in self.specs_dir.glob("*.md") if p.is_file()])
