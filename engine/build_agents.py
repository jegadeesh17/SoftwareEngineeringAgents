"""
Generate native sub-agent files for Claude Code and Antigravity from agents/.

Source of truth: agents/roles.toml (metadata) + agents/<role>.md (prompt bodies).
Run `python -m engine.build_agents` after editing agents/, or add --check to verify without writing.
"""

import argparse
import json
import re
import sys
import tomllib
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = Path("agents")
CLAUDE_AGENTS_DIR = Path(".claude") / "agents"
ANTIGRAVITY_AGENTS_DIR = Path(".agents") / "agents"
CLAUDE_COMMAND_PATH = Path("templates") / "claude" / "orchestrate.md"
GENERATED_MARKER = "<!-- GENERATED from agents/"

ALLOWED_KEYS = {
    "description", "claude_tools", "antigravity_tools", "main_agent", "claude_model",
    "runs_for", "delegate_when", "produces", "slots",
}
# Project facts a sub-agent can be gated on; the orchestrator records them in Phase 0
PROJECT_FACTS = ("always", "existing-code", "ui", "sensitive-data", "deploy")
# Workflow slots a sub-agent can fill; the orchestrator delegates by slot, so a new specialist needs no new workflow prose
SLOTS = ("discovery", "pipeline", "design-review", "task-owner", "milestone-review")
TEAM_TABLE_MARKER = "<!-- TEAM_TABLE -->"
# Claude Code model aliases; Antigravity output always inherits the session model
CLAUDE_MODELS = ("inherit", "opus", "sonnet", "haiku")
ROLE_NAME = re.compile(r"[a-z][a-z0-9-]*")
# Sub-agents are installed globally, so keep other sessions from routing unrelated work to them
SUBAGENT_SCOPE = " Part of the /orchestrate engineering team: use only when the orchestrator delegates to it."


@dataclass(frozen=True)
class Role:
    name: str
    description: str
    body: str
    antigravity_tools: List[str]
    claude_tools: Optional[List[str]] = None
    main_agent: bool = False
    claude_model: str = "inherit"
    runs_for: str = "always"
    delegate_when: str = ""
    produces: str = ""
    slots: List[str] = field(default_factory=list)


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n")


def display_name(name: str) -> str:
    """PascalCase display name for a kebab-case role id, e.g. ui-reviewer -> UiReviewer."""
    return "".join(part.capitalize() for part in name.split("-"))


def _is_string_list(value) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(v, str) and v.strip() for v in value)


def load_roles(source_dir: Path) -> List[Role]:
    manifest_path = source_dir / "roles.toml"
    if not manifest_path.exists():
        raise ValueError("agents/roles.toml not found")
    try:
        # utf-8-sig: editors such as PowerShell 5.1 prepend a BOM that TOML would reject
        entries = tomllib.loads(manifest_path.read_text(encoding="utf-8-sig")).get("roles", {})
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
        if not ROLE_NAME.fullmatch(name):
            raise ValueError(f"invalid role name '{name}': use lowercase letters, digits and hyphens")
        for required in ("description", "antigravity_tools"):
            if required not in entry:
                raise ValueError(f"role '{name}': '{required}' is required")
        if not isinstance(entry["description"], str) or not entry["description"].strip():
            raise ValueError(f"role '{name}': 'description' must be a non-empty string")
        main_agent = entry.get("main_agent", False)
        if not isinstance(main_agent, bool):
            raise ValueError(f"role '{name}': 'main_agent' must be true or false")
        if not main_agent and "claude_tools" not in entry:
            raise ValueError(f"role '{name}': sub-agents need 'claude_tools'")
        for key in ("claude_tools", "antigravity_tools"):
            if key in entry and not _is_string_list(entry[key]):
                raise ValueError(f"role '{name}': '{key}' must be a non-empty list of strings")
        if main_agent and "claude_model" in entry:
            raise ValueError(f"role '{name}': 'claude_model' applies to sub-agents only")
        claude_model = entry.get("claude_model", "inherit")
        if claude_model not in CLAUDE_MODELS:
            raise ValueError(f"role '{name}': 'claude_model' must be one of {', '.join(CLAUDE_MODELS)}")
        registry_keys = ("runs_for", "delegate_when", "produces", "slots")
        if main_agent and any(key in entry for key in registry_keys):
            raise ValueError(f"role '{name}': {', '.join(registry_keys)} apply to sub-agents only")
        if not main_agent:
            for key in registry_keys:
                if key not in entry:
                    raise ValueError(f"role '{name}': sub-agents need '{key}'")
            for key in ("delegate_when", "produces"):
                if not isinstance(entry[key], str) or not entry[key].strip():
                    raise ValueError(f"role '{name}': '{key}' must be a non-empty string")
            if entry["runs_for"] not in PROJECT_FACTS:
                raise ValueError(f"role '{name}': 'runs_for' must be one of {', '.join(PROJECT_FACTS)}")
            if not _is_string_list(entry["slots"]) or any(slot not in SLOTS for slot in entry["slots"]):
                raise ValueError(f"role '{name}': 'slots' must be a non-empty list drawn from {', '.join(SLOTS)}")
        body = normalize_newlines((source_dir / f"{name}.md").read_text(encoding="utf-8-sig")).strip() + "\n"
        roles.append(Role(
            name=name,
            description=entry["description"],
            body=body,
            antigravity_tools=list(entry["antigravity_tools"]),
            claude_tools=list(entry["claude_tools"]) if "claude_tools" in entry else None,
            main_agent=main_agent,
            claude_model=claude_model,
            runs_for=entry.get("runs_for", "always"),
            delegate_when=entry.get("delegate_when", ""),
            produces=entry.get("produces", ""),
            slots=list(entry.get("slots", [])),
        ))

    main_agents = [r for r in roles if r.main_agent]
    if len(main_agents) > 1:
        raise ValueError(f"only one main agent allowed, found: {', '.join(r.name for r in main_agents)}")
    for role in main_agents:
        if role.body.count(TEAM_TABLE_MARKER) != 1:
            raise ValueError(f"main agent body must contain {TEAM_TABLE_MARKER} exactly once")
    return roles


def render_team_table(roles: List[Role]) -> str:
    rows = [
        "| Agent | Id | Runs for | Slots | Delegate when | It produces |",
        "|---|---|---|---|---|---|",
    ]
    for role in sorted((r for r in roles if not r.main_agent), key=lambda r: r.name):
        rows.append(
            f"| {display_name(role.name)} | `{role.name}` | {role.runs_for} | {', '.join(role.slots)} | {role.delegate_when} | {role.produces} |"
        )
    return "\n".join(rows)


def _banner(role: Role) -> str:
    return f"{GENERATED_MARKER}{role.name}.md — edit the source and run python -m engine.build_agents -->\n\n"


def _yaml_string(value: str) -> str:
    # A JSON string is a valid YAML double-quoted scalar, so quotes and colons stay safe
    return json.dumps(value, ensure_ascii=False)


def _description(role: Role) -> str:
    return role.description if role.main_agent else role.description + SUBAGENT_SCOPE


def render_claude_agent(role: Role) -> str:
    return (
        "---\n"
        f"name: {role.name}\n"
        f"description: {_yaml_string(_description(role))}\n"
        f"tools: {', '.join(role.claude_tools)}\n"
        f"model: {role.claude_model}\n"
        "---\n\n"
        + _banner(role)
        + role.body
    )


def render_antigravity_agent(role: Role) -> str:
    tools = "".join(f"  - {tool}\n" for tool in role.antigravity_tools)
    return (
        "---\n"
        f"name: {role.name}\n"
        f"description: {_yaml_string(_description(role))}\n"
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
    table = render_team_table(roles)
    for role in roles:
        if role.main_agent:
            role = replace(role, body=role.body.replace(TEAM_TABLE_MARKER, table))
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


def find_orphans(outputs: Dict[Path, str], root: Path) -> List[Path]:
    """Generated files on disk that no longer correspond to a role.

    A file only counts as generated when its banner names its own role, so a hand-written
    agent copied from a generated one (banner and all) is never treated as an orphan.
    """
    orphans = []
    for base, pattern, role_of in (
        (CLAUDE_AGENTS_DIR, "*.md", lambda rel: rel.stem),
        (ANTIGRAVITY_AGENTS_DIR, "*/agent.md", lambda rel: rel.parent.name),
    ):
        if (root / base).exists():
            for path in (root / base).glob(pattern):
                rel = path.relative_to(root)
                text = _read_text(path)
                if rel not in outputs and text is not None and f"{GENERATED_MARKER}{role_of(rel)}.md —" in text:
                    orphans.append(rel)
    # The slash command belongs to whichever role is the main agent, so any generated banner counts
    command = root / CLAUDE_COMMAND_PATH
    if CLAUDE_COMMAND_PATH not in outputs and command.exists() and GENERATED_MARKER in (_read_text(command) or ""):
        orphans.append(CLAUDE_COMMAND_PATH)
    return sorted(orphans)


def _read_text(path: Path) -> Optional[str]:
    """File text with LF endings, or None if it is not UTF-8 (such files are never ours)."""
    try:
        return normalize_newlines(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return None


def find_stale(outputs: Dict[Path, str], root: Path) -> List[Path]:
    stale = [
        rel for rel, content in outputs.items()
        if not (root / rel).exists() or _read_text(root / rel) != content
    ]
    return sorted(stale + find_orphans(outputs, root))


def remove_orphans(outputs: Dict[Path, str], root: Path) -> None:
    for rel in find_orphans(outputs, root):
        path = root / rel
        path.unlink()
        if path.name == "agent.md" and not any(path.parent.iterdir()):
            path.parent.rmdir()


def main(argv: Optional[List[str]] = None, root: Optional[Path] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Claude Code and Antigravity agents from agents/")
    parser.add_argument("--check", action="store_true", help="exit 1 if generated files are out of date")
    args = parser.parse_args(argv)
    root = root or REPO_ROOT

    try:
        outputs = build_outputs(load_roles(root / SOURCE_DIR))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.check:
        stale = find_stale(outputs, root)
        if stale:
            print("Generated agent files are out of date (run: python -m engine.build_agents):")
            for rel in stale:
                print(f"  {rel.as_posix()}")
            return 1
        print("Generated agent files are up to date.")
        return 0

    write_outputs(outputs, root)
    remove_orphans(outputs, root)
    print(f"Wrote {len(outputs)} generated files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
