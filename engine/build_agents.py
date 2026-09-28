"""
Generate native sub-agent files for Claude Code and Antigravity from agents/.

Source of truth: agents/roles.toml (metadata) + agents/<role>.md (prompt bodies).
Run `python -m engine.build_agents` after editing agents/.
"""

import argparse
import json
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = Path("agents")
CLAUDE_AGENTS_DIR = Path(".claude") / "agents"
ANTIGRAVITY_AGENTS_DIR = Path(".agents") / "agents"
CLAUDE_COMMAND_PATH = Path("templates") / "claude" / "orchestrate.md"
GENERATED_MARKER = "<!-- GENERATED from agents/"

ALLOWED_KEYS = {"description", "claude_tools", "antigravity_tools", "main_agent"}


@dataclass(frozen=True)
class Role:
    name: str
    description: str
    body: str
    antigravity_tools: List[str]
    claude_tools: Optional[List[str]] = None
    main_agent: bool = False


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n")


def load_roles(source_dir: Path) -> List[Role]:
    manifest_path = source_dir / "roles.toml"
    if not manifest_path.exists():
        raise ValueError("agents/roles.toml not found")
    try:
        entries = tomllib.loads(manifest_path.read_text(encoding="utf-8")).get("roles", {})
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"agents/roles.toml is not valid TOML: {e}") from e

    prompt_names = {p.stem for p in source_dir.glob("*.md")}
    missing_prompts = sorted(set(entries) - prompt_names)
    if missing_prompts:
        raise ValueError(f"roles.toml lists roles without a prompt file: {', '.join(missing_prompts)}")
    unlisted = sorted(prompt_names - set(entries))
    if unlisted:
        raise ValueError(f"prompt files without a roles.toml entry: {', '.join(unlisted)}")

    roles = []
    for name in sorted(entries):
        entry = entries[name]
        unknown = sorted(set(entry) - ALLOWED_KEYS)
        if unknown:
            raise ValueError(f"role '{name}': unknown keys: {', '.join(unknown)}")
        for required in ("description", "antigravity_tools"):
            if required not in entry:
                raise ValueError(f"role '{name}': '{required}' is required")
        main_agent = entry.get("main_agent", False) is True
        if not main_agent and "claude_tools" not in entry:
            raise ValueError(f"role '{name}': sub-agents need 'claude_tools'")
        body = normalize_newlines((source_dir / f"{name}.md").read_text(encoding="utf-8")).strip() + "\n"
        roles.append(Role(
            name=name,
            description=entry["description"],
            body=body,
            antigravity_tools=list(entry["antigravity_tools"]),
            claude_tools=list(entry["claude_tools"]) if "claude_tools" in entry else None,
            main_agent=main_agent,
        ))

    main_agents = [r.name for r in roles if r.main_agent]
    if len(main_agents) > 1:
        raise ValueError(f"only one main agent allowed, found: {', '.join(main_agents)}")
    return roles


def _banner(role: Role) -> str:
    return f"{GENERATED_MARKER}{role.name}.md — edit the source and run python -m engine.build_agents -->\n\n"


def _yaml_string(value: str) -> str:
    # A JSON string is a valid YAML double-quoted scalar, so quotes and colons stay safe
    return json.dumps(value, ensure_ascii=False)


def render_claude_agent(role: Role) -> str:
    return (
        "---\n"
        f"name: {role.name}\n"
        f"description: {_yaml_string(role.description)}\n"
        f"tools: {', '.join(role.claude_tools)}\n"
        "model: inherit\n"
        "---\n\n"
        + _banner(role)
        + role.body
    )


def render_antigravity_agent(role: Role) -> str:
    tools = "".join(f"  - {tool}\n" for tool in role.antigravity_tools)
    return (
        "---\n"
        f"name: {role.name}\n"
        f"description: {_yaml_string(role.description)}\n"
        f"tools:\n{tools}"
        "model: inherit\n"
        f"mainAgent: {'true' if role.main_agent else 'false'}\n"
        f"subagent: {'false' if role.main_agent else 'true'}\n"
        "---\n\n"
        + _banner(role)
        + role.body
    )


def render_claude_command(role: Role) -> str:
    return (
        "---\n"
        f"description: {_yaml_string(role.description)}\n"
        "---\n\n"
        + _banner(role)
        + role.body
    )


def build_outputs(roles: List[Role]) -> Dict[Path, str]:
    outputs: Dict[Path, str] = {}
    for role in roles:
        outputs[ANTIGRAVITY_AGENTS_DIR / role.name / "agent.md"] = render_antigravity_agent(role)
        if role.main_agent:
            outputs[CLAUDE_COMMAND_PATH] = render_claude_command(role)
        else:
            outputs[CLAUDE_AGENTS_DIR / f"{role.name}.md"] = render_claude_agent(role)
    return outputs


def write_outputs(outputs: Dict[Path, str], root: Path) -> None:
    for rel, content in outputs.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


def main(argv: Optional[List[str]] = None, root: Optional[Path] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Claude Code and Antigravity agents from agents/")
    parser.parse_args(argv)
    root = root or REPO_ROOT

    try:
        outputs = build_outputs(load_roles(root / SOURCE_DIR))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    write_outputs(outputs, root)
    print(f"Wrote {len(outputs)} generated files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
