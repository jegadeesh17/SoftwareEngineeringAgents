# Native Sub-Agents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define the engineering team once in `agents/`, then generate native sub-agents from it for both Claude Code and Antigravity. The installer puts them in the global folders so the orchestrator can delegate to real sub-agents in any project, with no API keys.

**Architecture:** `agents/roles.toml` holds each role's metadata and `agents/<role>.md` holds its prompt. The generator `engine/build_agents.py` renders these into each runtime's frontmatter format and writes `.claude/agents/`, `.agents/agents/` and `templates/claude/orchestrate.md`. The generated files are committed. A `--check` mode and a test catch drift between source and output. `scripts/install_global.py` refuses to install stale output, then copies the generated files to `~/.claude/` and `~/.gemini/config/`.

**Tech Stack:** Python 3.11+ standard library only (`tomllib`, `argparse`, `json`, `pathlib`), pytest (dev extra).

**Spec:** `docs/superpowers/specs/2026-09-28-native-subagents-design.md`

## Global Constraints

- `requires-python = ">=3.11"` (for `tomllib`). No runtime dependencies. pytest only in the `dev` extra.
- No API keys and no model calls from Python.
- Generated files are never hand-edited. The generator writes UTF-8 with LF line endings.
- This machine has `git config core.autocrlf=true`: checked-out files can have CRLF, so every comparison must normalize `\r\n` to `\n`.
- Claude Code sub-agent frontmatter: `name`, `description`, `tools` (comma-separated string), `model: inherit`. Location `.claude/agents/<name>.md`, global `~/.claude/agents/<name>.md`.
- Antigravity agent frontmatter: `name`, `description`, `tools` (YAML list), `model: inherit`, `mainAgent`, `subagent`. Location `.agents/agents/<name>/agent.md`, global `~/.gemini/config/agents/<name>/agent.md`.
- The installer never deletes anything in the user's home directory. It keeps files that differ unless `--force` is passed.
- The orchestrator is a Claude Code **slash command** (`templates/claude/orchestrate.md`), not a Claude agent file. In Antigravity it is an agent with `mainAgent: true`, `subagent: false`.
- Every generated body starts with `<!-- GENERATED from agents/<role>.md — edit the source and run python -m engine.build_agents -->`.

## Review Focus

- **Windows checkout with CRLF source files.** Output must still be LF, and `--check` must pass on a CRLF checkout of the generated files. Tested in Task 1 (source) and Task 2 (checkout).
- **Descriptions containing quotes or colons.** The frontmatter must stay valid YAML. Tested in Task 1.
- **A typo in a `roles.toml` key** (e.g. `claude_tool`) must produce a clear error with nothing written. It must not silently drop the tool list. Tested in Task 1.
- **Renamed or removed role.** Its old generated files must be cleaned up, while hand-written agent files in the same folders are left alone. Tested in Task 2.
- **Edited `agents/` but forgot to regenerate, then ran the installer.** The installer must refuse, not install stale prompts. Tested in Task 4.

---

## File Structure

| Path | Responsibility |
|---|---|
| `engine/build_agents.py` (create) | Load and validate the source, render per runtime, write, check for drift, CLI |
| `tests/test_build_agents.py` (create) | Generator behavior on temporary source trees, plus a drift guard on the real repo |
| `agents/roles.toml`, `agents/*.md` (create) | The team: source of truth |
| `.claude/agents/*.md`, `.agents/agents/*/agent.md`, `templates/claude/orchestrate.md` (generated) | Runtime files, committed |
| `scripts/install_global.py` (rewrite) | Copy generated files into the global folders |
| `tests/test_install_global.py` (rewrite) | Installer behavior against a temporary home directory |
| `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md` (rewrite) | Developer guide and user docs |
| Delete: `.agents/skills/`, `.agents/rules/{psb-workflow-discipline,orchestrator-governance,qa-verification,git-discipline}.md`, `templates/antigravity/` | Replaced by `agents/` |

---

### Task 1: Generator — load, validate, render, write

**Files:**
- Create: `engine/build_agents.py`
- Create: `tests/test_build_agents.py`
- Modify: `pyproject.toml` (`requires-python`)

**Interfaces:**
- Produces (used by Tasks 2–4):
  - `build_agents.main(argv: list[str] | None = None, root: Path | None = None) -> int`. Returns 0 on success and 2 on invalid source; writes files under `root`, which defaults to the repo root and never the current directory.
  - `build_agents.load_roles(source_dir: Path) -> list[Role]`, raising `ValueError`.
  - `build_agents.build_outputs(roles: list[Role]) -> dict[Path, str]`, keyed by path relative to root.
  - `build_agents.Role`, a frozen dataclass with fields `name`, `description`, `body`, `antigravity_tools`, `claude_tools`, `main_agent`.
  - Constants: `REPO_ROOT`, `GENERATED_MARKER`, `CLAUDE_AGENTS_DIR`, `ANTIGRAVITY_AGENTS_DIR`, `CLAUDE_COMMAND_PATH`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_build_agents.py`:

```python
import pytest

from engine import build_agents

QA_TOML = """
[roles.qa-tester]
description = "Runs tests"
claude_tools = ["Read", "Bash"]
antigravity_tools = ["view_file", "run_command"]
"""

ORCH_TOML = """
[roles.orchestrator]
description = "Leads the team"
main_agent = true
antigravity_tools = ["view_file", "invoke_subagent"]
"""

QA_BANNER = (
    "<!-- GENERATED from agents/qa-tester.md — edit the source and run "
    "python -m engine.build_agents -->\n\n"
)


def make_source(root, toml_text, prompts):
    src = root / "agents"
    src.mkdir()
    (src / "roles.toml").write_text(toml_text, encoding="utf-8")
    for name, body in prompts.items():
        (src / f"{name}.md").write_text(body, encoding="utf-8")
    return root


def test_claude_agent_has_frontmatter_and_verbatim_body(tmp_path):
    make_source(tmp_path, QA_TOML, {"qa-tester": "# QA\n\nRun the tests.\n"})

    assert build_agents.main([], root=tmp_path) == 0

    text = (tmp_path / ".claude" / "agents" / "qa-tester.md").read_text(encoding="utf-8")
    assert text == (
        "---\n"
        "name: qa-tester\n"
        'description: "Runs tests"\n'
        "tools: Read, Bash\n"
        "model: inherit\n"
        "---\n\n"
        + QA_BANNER
        + "# QA\n\nRun the tests.\n"
    )


def test_antigravity_agent_lists_tools_and_is_a_subagent(tmp_path):
    make_source(tmp_path, QA_TOML, {"qa-tester": "# QA\n\nRun the tests.\n"})

    assert build_agents.main([], root=tmp_path) == 0

    text = (tmp_path / ".agents" / "agents" / "qa-tester" / "agent.md").read_text(encoding="utf-8")
    assert text == (
        "---\n"
        "name: qa-tester\n"
        'description: "Runs tests"\n'
        "tools:\n"
        "  - view_file\n"
        "  - run_command\n"
        "model: inherit\n"
        "mainAgent: false\n"
        "subagent: true\n"
        "---\n\n"
        + QA_BANNER
        + "# QA\n\nRun the tests.\n"
    )


def test_orchestrator_is_antigravity_main_agent_and_claude_slash_command(tmp_path):
    make_source(tmp_path, ORCH_TOML, {"orchestrator": "# Lead\n"})

    assert build_agents.main([], root=tmp_path) == 0

    agy = (tmp_path / ".agents" / "agents" / "orchestrator" / "agent.md").read_text(encoding="utf-8")
    assert "mainAgent: true\nsubagent: false\n" in agy
    assert "  - invoke_subagent\n" in agy
    command = (tmp_path / "templates" / "claude" / "orchestrate.md").read_text(encoding="utf-8")
    assert command == (
        "---\n"
        'description: "Leads the team"\n'
        "---\n\n"
        "<!-- GENERATED from agents/orchestrator.md — edit the source and run "
        "python -m engine.build_agents -->\n\n"
        "# Lead\n"
    )
    assert not (tmp_path / ".claude" / "agents").exists()


def test_description_with_quotes_and_colons_is_escaped(tmp_path):
    toml_text = QA_TOML.replace('"Runs tests"', "'Checks \"edge\" cases: all of them'")
    make_source(tmp_path, toml_text, {"qa-tester": "# QA\n"})

    assert build_agents.main([], root=tmp_path) == 0

    text = (tmp_path / ".claude" / "agents" / "qa-tester.md").read_text(encoding="utf-8")
    assert 'description: "Checks \\"edge\\" cases: all of them"\n' in text


def test_crlf_unicode_source_produces_lf_utf8_output(tmp_path):
    make_source(tmp_path, QA_TOML, {})
    (tmp_path / "agents" / "qa-tester.md").write_bytes("# QA\r\n\r\nFail fast — always.\r\n".encode("utf-8"))

    assert build_agents.main([], root=tmp_path) == 0

    data = (tmp_path / ".claude" / "agents" / "qa-tester.md").read_bytes()
    assert b"\r\n" not in data
    assert data.endswith("# QA\n\nFail fast — always.\n".encode("utf-8"))


@pytest.mark.parametrize(
    "toml_text, prompts, message",
    [
        (QA_TOML, {}, "without a prompt file: qa-tester"),
        (QA_TOML, {"qa-tester": "x", "extra": "y"}, "without a roles.toml entry: extra"),
        (QA_TOML.replace("claude_tools", "claude_tool"), {"qa-tester": "x"}, "unknown keys: claude_tool"),
        (QA_TOML.replace('claude_tools = ["Read", "Bash"]\n', ""), {"qa-tester": "x"}, "sub-agents need 'claude_tools'"),
        (QA_TOML.replace('description = "Runs tests"\n', ""), {"qa-tester": "x"}, "'description' is required"),
        (
            ORCH_TOML + ORCH_TOML.replace("orchestrator", "second-lead"),
            {"orchestrator": "x", "second-lead": "y"},
            "only one main agent allowed, found: orchestrator, second-lead",
        ),
        ("[roles.qa-tester\n", {"qa-tester": "x"}, "roles.toml"),
    ],
)
def test_invalid_source_is_rejected_and_nothing_written(tmp_path, capsys, toml_text, prompts, message):
    make_source(tmp_path, toml_text, prompts)

    assert build_agents.main([], root=tmp_path) == 2

    assert message in capsys.readouterr().err
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / ".agents").exists()


def test_missing_manifest_is_reported(tmp_path, capsys):
    (tmp_path / "agents").mkdir()

    assert build_agents.main([], root=tmp_path) == 2

    assert "agents/roles.toml not found" in capsys.readouterr().err
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_build_agents.py -q`
Expected: collection error `ImportError: cannot import name 'build_agents' from 'engine'`.

- [ ] **Step 3: Write the implementation**

Create `engine/build_agents.py`:

```python
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
```

In `pyproject.toml`, change `requires-python = ">=3.10"` to `requires-python = ">=3.11"`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest -q`
Expected: all tests pass (13 generator tests plus 3 existing installer tests).

- [ ] **Step 5: Commit**

```bash
git add engine/build_agents.py tests/test_build_agents.py pyproject.toml
git commit -m "feat(build): generate Claude Code and Antigravity agents from one source"
```

---

### Task 2: Generator — `--check` drift detection and cleanup of stale files

**Files:**
- Modify: `engine/build_agents.py`
- Test: `tests/test_build_agents.py` (append)

**Interfaces:**
- Consumes: `main`, `build_outputs`, `write_outputs`, `normalize_newlines`, `GENERATED_MARKER`, `CLAUDE_AGENTS_DIR`, `ANTIGRAVITY_AGENTS_DIR` from Task 1.
- Produces:
  - `build_agents.main(["--check"], root=...) -> int`: 0 if up to date, 1 if stale, 2 if the source is invalid. Stale paths are printed in POSIX form (e.g. `.claude/agents/qa-tester.md`).
  - `build_agents.find_stale(outputs: dict[Path, str], root: Path) -> list[Path]`.
  - `build_agents.find_orphans(outputs: dict[Path, str], root: Path) -> list[Path]`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_build_agents.py`:

```python
def test_check_fails_until_built_then_passes(tmp_path, capsys):
    make_source(tmp_path, QA_TOML, {"qa-tester": "# QA\n"})

    assert build_agents.main(["--check"], root=tmp_path) == 1
    assert ".claude/agents/qa-tester.md" in capsys.readouterr().out

    assert build_agents.main([], root=tmp_path) == 0
    assert build_agents.main(["--check"], root=tmp_path) == 0


def test_check_detects_hand_edited_generated_file(tmp_path):
    make_source(tmp_path, QA_TOML, {"qa-tester": "# QA\n"})
    build_agents.main([], root=tmp_path)
    generated = tmp_path / ".agents" / "agents" / "qa-tester" / "agent.md"
    with open(generated, "a", encoding="utf-8") as f:
        f.write("tweak\n")

    assert build_agents.main(["--check"], root=tmp_path) == 1


def test_check_accepts_crlf_checkout(tmp_path):
    make_source(tmp_path, QA_TOML, {"qa-tester": "# QA\n"})
    build_agents.main([], root=tmp_path)
    generated = tmp_path / ".claude" / "agents" / "qa-tester.md"
    generated.write_bytes(generated.read_bytes().replace(b"\n", b"\r\n"))

    assert build_agents.main(["--check"], root=tmp_path) == 0


def test_build_removes_stale_generated_agents_but_keeps_hand_written(tmp_path):
    make_source(tmp_path, QA_TOML, {"qa-tester": "# QA\n"})
    build_agents.main([], root=tmp_path)
    stale_text = (
        "---\nname: old-role\n---\n\n"
        "<!-- GENERATED from agents/old-role.md — edit the source and run python -m engine.build_agents -->\n\nold\n"
    )
    stale_claude = tmp_path / ".claude" / "agents" / "old-role.md"
    stale_claude.write_text(stale_text, encoding="utf-8")
    stale_agy = tmp_path / ".agents" / "agents" / "old-role" / "agent.md"
    stale_agy.parent.mkdir(parents=True)
    stale_agy.write_text(stale_text, encoding="utf-8")
    hand_written = tmp_path / ".claude" / "agents" / "my-helper.md"
    hand_written.write_text("---\nname: my-helper\n---\n\nhand written\n", encoding="utf-8")

    assert build_agents.main(["--check"], root=tmp_path) == 1
    assert build_agents.main([], root=tmp_path) == 0

    assert not stale_claude.exists()
    assert not stale_agy.parent.exists()
    assert hand_written.exists()
    assert build_agents.main(["--check"], root=tmp_path) == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_build_agents.py -q`
Expected: the 4 new tests FAIL. argparse exits with `unrecognized arguments: --check` (a `SystemExit: 2` error) for the three that pass `--check`, and the stale-file test fails when it reaches its first `--check` call.

- [ ] **Step 3: Write the implementation**

In `engine/build_agents.py`, add these functions after `write_outputs`:

```python
def find_orphans(outputs: Dict[Path, str], root: Path) -> List[Path]:
    """Generated files on disk that no longer correspond to a role. Hand-written files are never orphans."""
    candidates = []
    for base, pattern in ((CLAUDE_AGENTS_DIR, "*.md"), (ANTIGRAVITY_AGENTS_DIR, "*/agent.md")):
        if (root / base).exists():
            candidates += [p.relative_to(root) for p in (root / base).glob(pattern)]
    return sorted(
        rel for rel in candidates
        if rel not in outputs and GENERATED_MARKER in (root / rel).read_text(encoding="utf-8")
    )


def find_stale(outputs: Dict[Path, str], root: Path) -> List[Path]:
    stale = [
        rel for rel, content in outputs.items()
        if not (root / rel).exists()
        or normalize_newlines((root / rel).read_text(encoding="utf-8")) != content
    ]
    return sorted(stale + find_orphans(outputs, root))


def remove_orphans(outputs: Dict[Path, str], root: Path) -> None:
    for rel in find_orphans(outputs, root):
        path = root / rel
        path.unlink()
        if path.name == "agent.md" and not any(path.parent.iterdir()):
            path.parent.rmdir()
```

Replace `main` with:

```python
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
```

Update the module docstring's last line to:
`Run \`python -m engine.build_agents\` after editing agents/, or add --check to verify without writing.`

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest -q`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add engine/build_agents.py tests/test_build_agents.py
git commit -m "feat(build): add --check drift detection and remove stale generated agents"
```

---

### Task 3: The team — source prompts, generated agents, and retiring old skills and rules

**Files:**
- Create: `agents/roles.toml`, `agents/orchestrator.md`, `agents/product-analyst.md`, `agents/software-architect.md`, `agents/task-planner.md`, `agents/software-developer.md`, `agents/qa-tester.md`, `agents/adversarial-reviewer.md`, `agents/devops-git.md`
- Generate: `.claude/agents/*.md` (7), `.agents/agents/*/agent.md` (8), `templates/claude/orchestrate.md` (overwritten)
- Delete: `.agents/skills/` (all 7 dirs), `.agents/rules/psb-workflow-discipline.md`, `.agents/rules/orchestrator-governance.md`, `.agents/rules/qa-verification.md`, `.agents/rules/git-discipline.md`, `templates/antigravity/`
- Test: `tests/test_build_agents.py` (append)

**Interfaces:**
- Consumes: `build_agents.main`, `build_agents.load_roles`, `build_agents.REPO_ROOT` from Tasks 1–2.
- Produces: the committed generated files that Task 4 installs. Their names are `orchestrator`, `product-analyst`, `software-architect`, `task-planner`, `software-developer`, `qa-tester`, `adversarial-reviewer`, `devops-git`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_build_agents.py`:

```python
def test_committed_generated_files_match_source(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # the default root must be the repo, not the current directory

    assert build_agents.main(["--check"]) == 0


def test_team_roster_and_permissions():
    roles = {r.name: r for r in build_agents.load_roles(build_agents.REPO_ROOT / "agents")}

    assert set(roles) == {
        "orchestrator", "product-analyst", "software-architect", "task-planner",
        "software-developer", "qa-tester", "adversarial-reviewer", "devops-git",
    }
    assert [n for n, r in roles.items() if r.main_agent] == ["orchestrator"]
    # Without invoke_subagent the Antigravity orchestrator cannot delegate at all
    assert "invoke_subagent" in roles["orchestrator"].antigravity_tools
    # The reviewer must not be able to change the code it judges
    assert not {"Write", "Edit"} & set(roles["adversarial-reviewer"].claude_tools)
    assert not {"write_to_file", "replace_file_content"} & set(roles["adversarial-reviewer"].antigravity_tools)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_build_agents.py -q -k "committed or roster"`
Expected: both FAIL. `main` returns 2 because `agents/roles.toml not found`, and `load_roles` raises `ValueError`.

- [ ] **Step 3: Create `agents/roles.toml`**

```toml
# Source of truth for the agent team. After editing anything in agents/, run:
#   python -m engine.build_agents
# claude_tools uses Claude Code tool names; antigravity_tools uses Antigravity tool names.
# main_agent = true marks the orchestrator: an Antigravity main agent and the Claude Code /orchestrate command.

[roles.orchestrator]
description = "Lead Engineering Orchestrator and technical mentor: interviews the user, enforces the approval gate, delegates to the engineering sub-agents, and verifies every result."
main_agent = true
antigravity_tools = ["view_file", "write_to_file", "replace_file_content", "grep_search", "run_command", "invoke_subagent"]

[roles.product-analyst]
description = "Turns docs/PROJECT_MENTAL_MODEL.md into docs/SPEC.md with user journeys and Given/When/Then acceptance criteria. Use after the user approves the scope."
claude_tools = ["Read", "Write", "Edit", "Glob", "Grep"]
antigravity_tools = ["view_file", "write_to_file", "replace_file_content", "grep_search"]

[roles.software-architect]
description = "Designs the stack, components, data models, interfaces and test command in docs/ARCHITECTURE.md and records decisions in docs/DECISIONS.md. Use after docs/SPEC.md exists."
claude_tools = ["Read", "Write", "Edit", "Glob", "Grep"]
antigravity_tools = ["view_file", "write_to_file", "replace_file_content", "grep_search"]

[roles.task-planner]
description = "Breaks the architecture into ordered, testable tasks across milestones M1, M2 and M3 in docs/TASKS.json. Use after docs/ARCHITECTURE.md exists."
claude_tools = ["Read", "Write", "Edit", "Glob", "Grep"]
antigravity_tools = ["view_file", "write_to_file", "replace_file_content", "grep_search"]

[roles.software-developer]
description = "Implements exactly one task from docs/TASKS.json, or fixes it using failure output or review findings."
claude_tools = ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
antigravity_tools = ["view_file", "write_to_file", "replace_file_content", "grep_search", "run_command"]

[roles.qa-tester]
description = "Writes and runs automated tests for one task and records the exact command and exit code in docs/QA_RESULTS.json."
claude_tools = ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
antigravity_tools = ["view_file", "write_to_file", "replace_file_content", "grep_search", "run_command"]

[roles.adversarial-reviewer]
description = "Read-only reviewer that audits a finished milestone for edge cases, silent failures, contract drift and security issues, and returns APPROVED or REJECTED."
claude_tools = ["Read", "Glob", "Grep", "Bash"]
antigravity_tools = ["view_file", "grep_search", "run_command"]

[roles.devops-git]
description = "Commits an approved milestone's files as one Conventional Commit, staging only the listed files."
claude_tools = ["Read", "Glob", "Grep", "Bash"]
antigravity_tools = ["view_file", "grep_search", "run_command"]
```

- [ ] **Step 4: Create `agents/orchestrator.md`**

````markdown
# Lead Engineering Orchestrator & Technical Mentor

You lead a team of engineering sub-agents and guide the user, often a non-technical "vibe coder", through the PSB (Plan · Setup · Build) workflow. You are the only team member who talks to the user. You do not write product code yourself: you interview, agree scope with the user, delegate to sub-agents, and verify their results.

## Principles

- **Teach while building.** Explain trade-offs in plain English. At the end of each phase, give a 2–3 sentence **Engineering Takeaway** on why professional teams do this step.
- **Human approval gate.** Do not start the spec or any code until the user explicitly approves the scope. Never approve on the user's behalf.
- **No hallucinated success.** A task is done only when you have run its test command yourself and seen exit code 0. A sub-agent saying "tests pass" is not proof.
- **Files are the hand-off.** Sub-agents start with a blank context and cannot see this conversation. Everything they need must be in `docs/` or in your delegation message.

## Your team

| Sub-agent | Delegate when | It produces |
|---|---|---|
| `product-analyst` | scope is approved | `docs/SPEC.md` |
| `software-architect` | `docs/SPEC.md` exists | `docs/ARCHITECTURE.md`, `docs/DECISIONS.md` |
| `task-planner` | the architecture exists | `docs/TASKS.json` |
| `software-developer` | each task, and each fix | code for that task |
| `qa-tester` | after each implementation | tests and an entry in `docs/QA_RESULTS.json` |
| `adversarial-reviewer` | end of each milestone | a verdict and findings, returned to you |
| `devops-git` | after a milestone is approved | one Conventional Commit |

## Delegation message

Every delegation states:

1. **Task:** one sentence.
2. **Read:** the exact files to read.
3. **Write:** the exact files or directories it may create or change.
4. **Return:** what to report back to you.

## Workflow

### Phase 0: Pre-flight scoping

1. Ask for the user's vision. Classify the posture as **Prototype** (speed, thinnest working slice) or **Production** (validation, typed schemas, thorough tests), and confirm it with the user.
2. Propose three milestones: **M1: MVP vertical slice** (the thinnest end-to-end path), **M2: Core flows**, **M3: Polish and edge cases**.
3. Create `docs/PROJECT_MENTAL_MODEL.md` (vision, posture, target persona, milestones) and `docs/PROJECT_STATUS.md` containing the checklist below, all unchecked.

### Phase 1: Spec interview

1. Ask these three questions together:
   - **Primary journey:** step by step, what does the user do and see?
   - **Errors and edge cases:** what should happen with invalid, empty or missing input?
   - **Non-goals:** what is explicitly out of scope for M1?
2. Record the answers in `docs/PROJECT_MENTAL_MODEL.md` under "Part 1: Requirements and UX".
3. Present a scope summary with the main trade-offs, then ask: *"Do you approve this scope and authorize the engineering team to proceed?"* Stop and wait. Anything other than a clear yes means the conversation continues.

### Phase 2: Planning (only after approval)

Delegate in order, and read each output before starting the next: `product-analyst`, then `software-architect`, then `task-planner`. If an output is missing or empty, delegate once more and state the problem. If it is still wrong, tell the user.

### Phase 3: Build loop

For each milestone in `docs/TASKS.json`, take each task in order:

1. Delegate the task to `software-developer`.
2. Delegate verification to `qa-tester`.
3. Read the task's newest entry in `docs/QA_RESULTS.json`. If `exit_code` is not 0, send its `failure_output` back to `software-developer` and repeat from step 2. After **3 failed attempts** on the same task, stop and ask the user how to proceed.
4. Run the recorded `command` yourself. Only if it exits 0, set the task's `status` to `"completed"` in `docs/TASKS.json`.

When every task in the milestone is completed:

5. Delegate to `adversarial-reviewer` with the milestone ID and the files changed in this milestone. Append its report to `docs/ADVERSARIAL_REVIEW.md`, one section per milestone.
6. If the verdict is **REJECTED**, turn each critical defect into a fix for `software-developer`, verify it with `qa-tester`, and request a new review.
7. If the verdict is **APPROVED**, delegate to `devops-git` with the milestone's files (including `docs/`) and a commit message such as `feat(m1): <what the milestone delivers>`. Tick the milestone in `docs/PROJECT_STATUS.md` and give an Engineering Takeaway.

### Phase 4: Handover

1. Run the full test suite yourself. It must exit 0.
2. Tick the remaining items in `docs/PROJECT_STATUS.md`.
3. Tell the user how to run the project, what was built, and briefly how the pieces fit together.

## `docs/PROJECT_STATUS.md` checklist

```markdown
# Project Status

- [ ] Phase 0: Scoping (posture and milestones agreed)
- [ ] Phase 1: Spec interview and user approval
- [ ] Phase 2.1: docs/SPEC.md
- [ ] Phase 2.2: docs/ARCHITECTURE.md and docs/DECISIONS.md
- [ ] Phase 2.3: docs/TASKS.json
- [ ] Phase 3.1: M1 built, verified, reviewed and committed
- [ ] Phase 3.2: M2 built, verified, reviewed and committed
- [ ] Phase 3.3: M3 built, verified, reviewed and committed
- [ ] Phase 4: Final test run and handover
```

Tick an item only when its evidence exists on disk. For build items, tick only after your own test run.

## Living documents

All eight live in the project's `docs/` folder: `PROJECT_MENTAL_MODEL.md`, `PROJECT_STATUS.md`, `SPEC.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `TASKS.json`, `QA_RESULTS.json`, `ADVERSARIAL_REVIEW.md`.

## Naming conventions to pass on

- Python: `snake_case.py` modules and functions, `PascalCase` classes, `UPPER_SNAKE_CASE` constants.
- TypeScript: `PascalCase.tsx` components, `camelCase.ts` utilities.
- Commits: Conventional Commits, `<type>(<scope>): <imperative description>`.
````

- [ ] **Step 5: Create `agents/product-analyst.md`**

```markdown
# Product Analyst

You turn the orchestrator's scoping notes into an unambiguous product specification. You do not talk to the user. If information is missing, list it under "Open questions" with the assumption you made; do not invent requirements silently.

## Read

- `docs/PROJECT_MENTAL_MODEL.md`

## Write

- `docs/SPEC.md` only. Do not create or change any other file.

## `docs/SPEC.md` structure

1. **Summary:** vision, posture (Prototype or Production), target persona.
2. **User journeys:** numbered steps describing what the user does and sees.
3. **Acceptance criteria:** Given / When / Then. At least one per journey step and one per error case in the mental model. Each criterion must be checkable by an automated test.
4. **Non-goals.**
5. **Open questions:** anything ambiguous, with the assumption you made.

## Return

A 3–5 line summary: the number of journeys, the number of acceptance criteria, and any open questions.
```

- [ ] **Step 6: Create `agents/software-architect.md`**

```markdown
# Software Architect

You design the technical foundation before any code is written.

## Read

- `docs/SPEC.md` and `docs/PROJECT_MENTAL_MODEL.md`.
- Existing source files, if the project already has code.

## Write

- `docs/ARCHITECTURE.md` and `docs/DECISIONS.md` only.

## `docs/ARCHITECTURE.md`

- **Technology stack:** language, framework, test runner, and the exact command that runs the tests (for example `python -m pytest -q`).
- **Components:** a Mermaid diagram and one line per component.
- **Data models:** typed fields and validation rules.
- **Interfaces:** function signatures, CLI commands or API endpoints, with inputs, outputs and errors.
- **Directory layout**, including where tests live.
- **Configuration:** environment variables, to be listed in `.env.example` (describe it here; the developer creates it).

Match the posture. For a Prototype, use the fewest moving parts and prefer the standard library. For Production, validate input at every boundary.

## `docs/DECISIONS.md`

One ADR per significant choice, with: Title, Status (Accepted), Context, Decision, Alternatives considered, Consequences. Write for a non-technical reader.

## Return

The stack, the test command, and the list of ADR titles.
```

- [ ] **Step 7: Create `agents/task-planner.md`**

````markdown
# Task Planner

You turn the architecture into an ordered backlog across three milestones.

## Read

- `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/PROJECT_MENTAL_MODEL.md`

## Write

- `docs/TASKS.json` only.

## Rules

- Exactly three milestones:
  - **M1: MVP vertical slice.** The thinnest end-to-end path through the primary journey, including at least one test.
  - **M2: Core flows.**
  - **M3: Polish and edge cases.**
- Each task can be implemented and tested in one sitting and touches few files.
- Each task's `acceptance_criteria` names the SPEC criteria it satisfies and how a test will check them.
- Order tasks so that each depends only on earlier tasks.
- Every task starts with `"status": "pending"`.

## Format

```json
{
  "milestones": [
    {
      "milestone_id": "M1",
      "name": "MVP vertical slice",
      "tasks": [
        {
          "id": "M1-TASK-01",
          "title": "Short title",
          "description": "Specific implementation instructions",
          "files_to_create": ["src/models.py"],
          "files_to_modify": [],
          "acceptance_criteria": "SPEC AC-1: a test that checks ...",
          "status": "pending"
        }
      ]
    }
  ]
}
```

## Return

The number of tasks per milestone and the first task's ID.
````

- [ ] **Step 8: Create `agents/software-developer.md`**

```markdown
# Software Developer

You implement exactly one task from `docs/TASKS.json`.

## Read

- The task named in your delegation message, in `docs/TASKS.json`.
- `docs/ARCHITECTURE.md` for contracts, layout and conventions.
- The existing code you will change or call.
- On a fix attempt: the failure output or review findings in your delegation message.

## Write

- Only the files listed in the task's `files_to_create` and `files_to_modify`. If another file must change, change it only when necessary and report it.

## Rules

- Follow the interfaces in `docs/ARCHITECTURE.md` exactly. If one is wrong, report it instead of silently deviating.
- Validate input at boundaries: handle empty, missing and malformed values.
- Never swallow errors (no bare `except: pass`, no empty `catch`).
- No hard-coded secrets. Read configuration from environment variables.
- Naming: in Python, `snake_case.py` modules and functions, `PascalCase` classes, `UPPER_SNAKE_CASE` constants. In TypeScript, `PascalCase.tsx` components and `camelCase.ts` utilities.
- On a fix attempt, fix the root cause shown in the failure, not the symptom. Never weaken or delete tests to make them pass.
- You may run code to check your work, but QA's run is the official verification.
- Do not commit.

## Return

The files you changed (one line each), and anything that deviates from the task or the architecture.
```

- [ ] **Step 9: Create `agents/qa-tester.md`**

````markdown
# QA Tester

You prove, by running real commands, whether one task works.

## Read

- The task and its `acceptance_criteria` in `docs/TASKS.json`.
- The matching acceptance criteria in `docs/SPEC.md`.
- The test command in `docs/ARCHITECTURE.md`.
- The implementation files for the task.

## Write

- Test files in the project's tests directory.
- `docs/QA_RESULTS.json` (append only; create it as `[]` if missing).
- Never change implementation files. If the code is wrong, the test should fail.

## Steps

1. Write or update tests that cover each acceptance criterion of the task, including at least one invalid-input case.
2. Run the test command from `docs/ARCHITECTURE.md` in the terminal.
3. Append one entry to `docs/QA_RESULTS.json`:

```json
{"task_id": "M1-TASK-01", "attempt": 1, "command": "python -m pytest -q", "exit_code": 0, "summary": "5 passed", "failure_output": ""}
```

`failure_output` holds the last 50 or so lines of output when `exit_code` is not 0.

## Rules

- Record the real exit code. Never report a pass you did not observe.
- A test that cannot fail is not a test: assert on real outputs.

## Return

The command, the exit code, and the summary line.
````

- [ ] **Step 10: Create `agents/adversarial-reviewer.md`**

````markdown
# Adversarial Reviewer

Your mindset: assume the code is broken until proven otherwise. You review; you do not fix. You cannot write files, so return your report to the orchestrator.

## Read

- The milestone's tasks in `docs/TASKS.json` and the changed files named in your delegation message.
- `docs/SPEC.md` and `docs/ARCHITECTURE.md`.
- `docs/QA_RESULTS.json`.

## Check

1. **Edge cases:** null or None, empty strings, oversized input, wrong types, missing files.
2. **Silent failures:** swallowed exceptions, ignored return codes, unhandled promise rejections.
3. **Contract drift:** does the code match the interfaces in `docs/ARCHITECTURE.md` and the criteria in `docs/SPEC.md`?
4. **Security:** hard-coded secrets; unsanitized input reaching a shell, SQL, HTML or file paths; secrets in logs.
5. **Verification proof:** re-run the test command yourself. Are the tests real, or do they assert nothing?

You may run commands to probe behavior (the tests, small scripts), but never create, modify or delete files.

## Return (exactly this format)

```
## Milestone <ID> Review
Verdict: APPROVED | REJECTED
Test command: <command> -> exit code <n>

### Critical defects (must fix; any defect means REJECTED)
- <file:line>: <problem>. <why it matters to the user>

### Recommendations (non-blocking)
- <suggestion>
```

Reject only for real defects that would harm a user or break the spec, not for style.
````

- [ ] **Step 11: Create `agents/devops-git.md`**

```markdown
# DevOps & Git

You record each approved milestone as one clean commit.

## Read

- The milestone ID, the file list and the commit message in your delegation message.

## Steps

1. If the project is not a git repository, run `git init`.
2. Run `git status` and compare it with the file list.
3. Stage only the listed files: `git add -- <files>`. Never use `git add .` or `git add -A`.
4. Run `git diff --cached --name-only`. If anything staged is a `.env` file, a key or a credential, stop and report it without committing.
5. Commit with the given message in Conventional Commits form, for example `git commit -m "feat(m1): add CSV import vertical slice"`.

## Rules

- Never force-push, rewrite history, amend commits or skip hooks.
- Never create or modify files; you only stage and commit. If a hook fails, report its output.
- If `.gitignore` is missing, report it; do not create it.

## Return

The commit hash and message, or the exact error output.
```

- [ ] **Step 12: Generate the runtime files and retire the old skills, rules and template**

Run:
```bash
python -m engine.build_agents
git rm -rq .agents/skills templates/antigravity .agents/rules/psb-workflow-discipline.md .agents/rules/orchestrator-governance.md .agents/rules/qa-verification.md .agents/rules/git-discipline.md
```
Expected: `Wrote 16 generated files.` That's 7 Claude agents, 8 Antigravity agents and 1 command. `.agents/rules/nomenclature-standards.md` remains.

- [ ] **Step 13: Run the tests to verify they pass**

Run: `python -m pytest -q`
Expected: all pass, including `test_committed_generated_files_match_source` and `test_team_roster_and_permissions`.

Note: `tests/test_install_global.py::test_installer_overwrites_customized_slash_command_with_force` still passes because it compares against the regenerated `templates/claude/orchestrate.md`.

- [ ] **Step 14: Commit**

```bash
git add agents .claude/agents .agents/agents templates/claude/orchestrate.md tests/test_build_agents.py
git commit -m "feat(agents): define the engineering team as native sub-agents for Claude Code and Antigravity"
```

---

### Task 4: Installer — install the generated team globally

**Files:**
- Modify (rewrite): `scripts/install_global.py`
- Test (rewrite): `tests/test_install_global.py`

**Interfaces:**
- Consumes: `build_agents.main(["--check"], root=...)`, which returns 0 when current (Task 2), and the generated files from Task 3.
- Produces: `install_global.main(argv: list[str] | None = None, home: Path | None = None, root: Path | None = None) -> int`. Returns 0 on success and 1 if the generated files are stale. Flags: `--force`, `--global-rules`.

- [ ] **Step 1: Write the failing tests**

Replace the whole of `tests/test_install_global.py` with:

```python
import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


@pytest.fixture
def installer(monkeypatch):
    # The installer must never shell out. Record instead of running, so a regression
    # (like the old `pip install -e`) fails the test without touching the real environment.
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: calls.append(a))
    spec = importlib.util.spec_from_file_location("install_global", ROOT / "scripts" / "install_global.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module
    assert calls == [], f"installer ran a subprocess: {calls}"


def test_installer_installs_team_for_both_tools(tmp_path, installer):
    assert installer.main([], home=tmp_path) == 0

    assert (tmp_path / ".claude" / "agents" / "qa-tester.md").read_bytes() == \
        (ROOT / ".claude" / "agents" / "qa-tester.md").read_bytes()
    assert (tmp_path / ".claude" / "commands" / "orchestrate.md").read_bytes() == \
        (ROOT / "templates" / "claude" / "orchestrate.md").read_bytes()
    assert (tmp_path / ".gemini" / "config" / "agents" / "orchestrator" / "agent.md").read_bytes() == \
        (ROOT / ".agents" / "agents" / "orchestrator" / "agent.md").read_bytes()
    assert len(list((tmp_path / ".claude" / "agents").glob("*.md"))) == 7
    assert len(list((tmp_path / ".gemini" / "config" / "agents").glob("*/agent.md"))) == 8


def test_installer_keeps_customized_slash_command(tmp_path, installer):
    existing = tmp_path / ".claude" / "commands" / "orchestrate.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("my customized command\n", encoding="utf-8")

    installer.main([], home=tmp_path)

    assert existing.read_text(encoding="utf-8") == "my customized command\n"


def test_installer_overwrites_customized_slash_command_with_force(tmp_path, installer):
    existing = tmp_path / ".claude" / "commands" / "orchestrate.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("my customized command\n", encoding="utf-8")

    installer.main(["--force"], home=tmp_path)

    assert existing.read_bytes() == (ROOT / "templates" / "claude" / "orchestrate.md").read_bytes()


def test_installer_skips_global_naming_rule_unless_requested(tmp_path, installer):
    rule = tmp_path / ".gemini" / "config" / "rules" / "nomenclature-standards.md"

    installer.main([], home=tmp_path)
    assert not rule.exists()

    installer.main(["--global-rules"], home=tmp_path)
    assert rule.exists()


def test_installer_rerun_skips_nothing(tmp_path, installer, capsys):
    installer.main([], home=tmp_path)
    capsys.readouterr()

    assert installer.main([], home=tmp_path) == 0

    assert "Skipped:" not in capsys.readouterr().out


def test_installer_flags_old_orchestrator_skill_without_deleting_it(tmp_path, installer, capsys):
    old_skill = tmp_path / ".gemini" / "config" / "skills" / "orchestrator" / "SKILL.md"
    old_skill.parent.mkdir(parents=True)
    old_skill.write_text("old skill\n", encoding="utf-8")

    installer.main([], home=tmp_path)

    assert old_skill.exists()
    assert "old 'orchestrator' skill" in capsys.readouterr().out


def test_installer_refuses_when_generated_files_are_stale(tmp_path, installer):
    repo = tmp_path / "repo"
    for name in ("agents", ".claude", ".agents", "templates"):
        shutil.copytree(ROOT / name, repo / name)
    with open(repo / "agents" / "qa-tester.md", "a", encoding="utf-8") as f:
        f.write("\nA new rule nobody regenerated.\n")
    home = tmp_path / "home"

    assert installer.main([], home=home, root=repo) == 1

    assert not home.exists()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_install_global.py -q`
Expected: every test fails or errors. The old installer still calls `pip install -e` when `--no-pip` isn't passed; the fixture records that call instead of running it and fails at teardown. In addition, `test_installer_installs_team_for_both_tools` finds no `.claude/agents` and `main` returns `None`, and `test_installer_refuses_when_generated_files_are_stale` fails with `TypeError: main() got an unexpected keyword argument 'root'`. Confirm that no `pip` output appears in the run.

- [ ] **Step 3: Write the implementation**

Replace the whole of `scripts/install_global.py` with:

```python
"""
Global Installer for SoftwareEngineeringAgents
Installs the generated agent team so it works in any project folder:
1. Claude Code sub-agents   -> ~/.claude/agents/<role>.md
2. Claude Code /orchestrate -> ~/.claude/commands/orchestrate.md
3. Antigravity agents       -> ~/.gemini/config/agents/<role>/agent.md
4. Antigravity global rule 'nomenclature-standards.md' (opt-in via --global-rules)

Existing files that differ from the generated ones are kept unless --force is passed.
Nothing in your home directory is ever deleted.
"""

import argparse
import filecmp
import shutil
import sys
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from engine import build_agents  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def install_file(src: Path, dst: Path, force: bool) -> bool:
    """Copy src to dst, refusing to clobber a customized dst unless force is set."""
    if dst.exists() and not force and not filecmp.cmp(src, dst, shallow=False):
        print(f"      [!] Skipped: {dst} exists and differs from the generated file (re-run with --force to overwrite)")
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"      [OK] Installed: {dst}")
    return True


def main(argv: Optional[List[str]] = None, home: Optional[Path] = None, root: Optional[Path] = None) -> int:
    parser = argparse.ArgumentParser(description="Install the SoftwareEngineeringAgents team globally")
    parser.add_argument("--force", action="store_true", help="overwrite existing files that differ from the generated ones")
    parser.add_argument("--global-rules", action="store_true",
                        help="also install the always-on nomenclature rule for every Antigravity project")
    args = parser.parse_args(argv)

    root = root or REPO_ROOT
    user_home = home or Path.home()

    print("=" * 65)
    print("  SOFTWARE ENGINEERING AGENTS: GLOBAL INSTALLER")
    print("=" * 65)

    if build_agents.main(["--check"], root=root) != 0:
        print("\n[!] Nothing installed: generated agent files are out of date with agents/.")
        print("    Run: python -m engine.build_agents")
        return 1

    print("\n[1/4] Claude Code sub-agents...")
    for src in sorted((root / ".claude" / "agents").glob("*.md")):
        install_file(src, user_home / ".claude" / "agents" / src.name, args.force)

    print("\n[2/4] Claude Code /orchestrate command...")
    install_file(root / "templates" / "claude" / "orchestrate.md",
                 user_home / ".claude" / "commands" / "orchestrate.md", args.force)

    print("\n[3/4] Antigravity agents...")
    for src in sorted((root / ".agents" / "agents").glob("*/agent.md")):
        install_file(src, user_home / ".gemini" / "config" / "agents" / src.parent.name / "agent.md", args.force)
    old_skill = user_home / ".gemini" / "config" / "skills" / "orchestrator"
    if old_skill.exists():
        print(f"      [!] Found the old 'orchestrator' skill at {old_skill}.")
        print("          The orchestrator agent replaces it; delete that folder to avoid two orchestrators.")

    print("\n[4/4] Antigravity global naming rule...")
    if not args.global_rules:
        print("      [-] Not installed: this rule applies to every project (re-run with --global-rules to install).")
    else:
        install_file(root / ".agents" / "rules" / "nomenclature-standards.md",
                     user_home / ".gemini" / "config" / "rules" / "nomenclature-standards.md", args.force)

    print("\n" + "=" * 65)
    print("  INSTALLATION COMPLETE")
    print("=" * 65)
    print("Start the team in any project folder:")
    print("  Claude Code:  run 'claude', then type /orchestrate")
    print("  Antigravity:  run 'agy --agent orchestrator'")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/install_global.py tests/test_install_global.py
git commit -m "feat(install): install generated sub-agents for Claude Code and Antigravity"
```

---

### Task 5: Documentation

**Files:**
- Modify (rewrite): `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`
- Modify: `requirements.txt`

These are prose files, so there are no tests. Verification is the stale-reference search in Step 5.

- [ ] **Step 1: Replace `AGENTS.md`**

````markdown
# SoftwareEngineeringAgents: Developer Guide

This repository **defines** an AI engineering team. It is not where the team builds projects: users install the team and run it inside their own project folders.

## Layout

| Path | What it is |
|---|---|
| `agents/roles.toml`, `agents/*.md` | **Source of truth.** Role metadata and one prompt per role. Edit here. |
| `.claude/agents/`, `.agents/agents/`, `templates/claude/orchestrate.md` | **Generated.** Never edit by hand. |
| `engine/build_agents.py` | Generator: renders `agents/` into each tool's format. |
| `scripts/install_global.py` | Installer: copies generated files into `~/.claude/` and `~/.gemini/config/`. |
| `.agents/rules/nomenclature-standards.md` | Optional global naming rule (installed with `--global-rules`). |
| `docs/superpowers/` | Design specs and implementation plans. |

## Changing the team

1. Edit `agents/roles.toml` or `agents/<role>.md`.
2. Regenerate: `python -m engine.build_agents`
3. Test: `python -m pytest -q`. This includes a drift check that fails if the generated files are stale.
4. Commit the source and the generated files together.

Requires Python 3.11+. Dev dependencies: `pip install -e ".[dev]"`.

## Tool names

- `claude_tools` use Claude Code names: `Read`, `Write`, `Edit`, `Glob`, `Grep`, `Bash`.
- `antigravity_tools` use Antigravity names: `view_file`, `write_to_file`, `replace_file_content`, `grep_search`, `run_command`, `invoke_subagent`.
- The orchestrator (`main_agent = true`) has no Claude tool list: in Claude Code it runs as the main session via `/orchestrate`.
````

- [ ] **Step 2: Replace `CLAUDE.md` and `GEMINI.md`**

`CLAUDE.md` (Claude Code imports the file referenced with `@`):

```markdown
@AGENTS.md
```

`GEMINI.md` (Antigravity already reads `AGENTS.md`; this file only points there):

```markdown
# Antigravity workspace notes

See `AGENTS.md` for the developer guide. Agent prompts live in `agents/`; the files in `.agents/agents/` are generated from them.
```

- [ ] **Step 3: Replace `README.md`**

````markdown
# SoftwareEngineeringAgents

> An AI software engineering team for non-technical builders ("vibe coders"). It runs natively inside **Claude Code** and **Google Antigravity** and needs no API keys.

You talk to one **Lead Engineering Orchestrator**. It interviews you and waits for your approval. Then it delegates the work to specialist sub-agents, each with its own context and tool permissions, and checks every result by running the tests itself. Along the way it explains *why* professional teams work this way.

## How it works

```
You <──> ORCHESTRATOR (the only agent that talks to you)
          1. Interviews you: vision, prototype vs production, UX, errors, non-goals
          2. Writes docs/PROJECT_MENTAL_MODEL.md and docs/PROJECT_STATUS.md
          3. STOPS: "Do you approve this scope?"  <- nothing is built without your yes
          │
          ├─> product-analyst ────────> docs/SPEC.md
          ├─> software-architect ─────> docs/ARCHITECTURE.md, docs/DECISIONS.md
          ├─> task-planner ───────────> docs/TASKS.json (M1 MVP -> M2 Core -> M3 Polish)
          │
          │   for each task:
          ├─> software-developer ─────> writes the code
          ├─> qa-tester ──────────────> writes and runs tests -> docs/QA_RESULTS.json
          │     fail -> back to the developer (up to 3 tries, then it asks you)
          │     pass -> the orchestrator re-runs the test itself before ticking it off
          │
          │   for each milestone:
          ├─> adversarial-reviewer ───> read-only audit -> APPROVED or REJECTED
          └─> devops-git ─────────────> commits only that milestone's files
```

## The team

| Agent | Produces | Can change files? |
|---|---|---|
| Orchestrator | the interview, approvals, status tracking | docs only (by instruction), and runs the tests |
| Product Analyst | `docs/SPEC.md` | docs only |
| Software Architect | `docs/ARCHITECTURE.md`, `docs/DECISIONS.md` | docs only |
| Task Planner | `docs/TASKS.json` | docs only |
| Software Developer | the code | yes, and can run commands |
| QA Tester | tests and `docs/QA_RESULTS.json` | tests and docs, and can run commands |
| Adversarial Reviewer | APPROVED/REJECTED verdict | **no**: read-only, can run tests |
| DevOps & Git | one commit per milestone | no: stages and commits only |

## Install

Requirements: Python 3.11+ (for the installer only), plus Claude Code and/or the Antigravity CLI.

```bash
# from a clone of this repository
python scripts/install_global.py
```

This installs:
- `~/.claude/agents/*.md`: the 7 Claude Code sub-agents.
- `~/.claude/commands/orchestrate.md`: the `/orchestrate` command.
- `~/.gemini/config/agents/*/agent.md`: the orchestrator and 7 sub-agents for Antigravity.

Options:
- `--force` overwrites files you've customized. Without it they are kept.
- `--global-rules` also installs an always-on naming-convention rule for every Antigravity project.

## Use

Open an empty folder for your new project, then:

- **Claude Code:** run `claude` and type `/orchestrate`.
- **Antigravity:** run `agy --agent orchestrator`, or pick `orchestrator` in `/agents`.

At the end you have working code, passing tests, one git commit per milestone, and eight documents in `docs/` explaining what was built and why.

## Customize the team

The prompts live in `agents/`. See [AGENTS.md](AGENTS.md) for how to edit and regenerate them.

## Limitations

- In Claude Code, sub-agents cannot start other sub-agents, so the orchestrator is your main session. It follows the process because its instructions say so, and you can talk it out of it.
- "Planning agents only write to `docs/`" is an instruction, not a hard limit. Those agents have no shell access.
- Antigravity's custom-agent format is new. If it changes, only `engine/build_agents.py` needs updating.

## License

MIT (see [LICENSE](LICENSE)).
````

- [ ] **Step 4: Update `requirements.txt`**

Replace its contents with:

```text
# Development dependencies (the project has no runtime dependencies)
pytest>=8.0.0
```

- [ ] **Step 5: Verify no stale references remain**

Run: `git grep -nE "engine\.cli|engine/cli|orchestrate\.exe|se-agents|PRD\.md|\.agents/skills|psb-workflow|orchestrator-governance|qa-verification|git-discipline|templates/antigravity|OpenInference" -- . ":(exclude)docs/superpowers"`
Expected: no output.

Run: `python -m pytest -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add AGENTS.md CLAUDE.md GEMINI.md README.md requirements.txt
git commit -m "docs: describe the native sub-agent team and how to develop it"
```

---

### Task 6: Live verification (needs the user's go-ahead; uses their Claude and Antigravity subscriptions)

**Files:** possibly `agents/roles.toml` (tool-name fixes), then regenerated output.

Ask the user before starting this task. Steps 1–5 write to their home directory and consume their subscription quota.

- [ ] **Step 1: Install for real**

Run: `python scripts/install_global.py --force`
`--force` is needed because an older `~/.claude/commands/orchestrate.md` from the previous installer exists and differs.
Expected: `INSTALLATION COMPLETE`, and the notice about the old `orchestrator` skill. Tell the user they can delete `~/.gemini/config/skills/orchestrator/`.

- [ ] **Step 2: Claude Code discovery**

In a scratch folder (under the session scratchpad), run:
`claude -p "List the names of the custom subagents available to you, one per line, nothing else."`
Expected: the 7 role names.

- [ ] **Step 3: Antigravity discovery**

In the same scratch folder, run:
`agy -p "List the names of the custom agents and subagents available to you, one per line, nothing else."`
Expected: `orchestrator` and the 7 role names.

- [ ] **Step 4: Antigravity tool names and sandbox**

In the scratch folder, run:
`agy --agent orchestrator -p "Delegate to the qa-tester subagent: run 'python --version' in the terminal and report the exact command and exit code. Then report its answer verbatim."`
Expected: the output shows the command ran with exit code 0.
- If a tool name is rejected, fix it in `agents/roles.toml`, run `python -m engine.build_agents`, then `python -m pytest -q`, and commit `fix(agents): correct Antigravity tool names`.
- If `run_command` is blocked by the sandbox, stop and report to the user. The spec's fallback (`commandExecutionPolicy: auto` for developer and qa-tester) needs a new `roles.toml` key, with a generator test first.

- [ ] **Step 5: End-to-end run**

In a fresh scratch folder, start `/orchestrate` (Claude Code), then `agy --agent orchestrator` (Antigravity). Use the idea *"a command-line tool that counts words in a text file"*, posture Prototype, and approve the scope. Confirm in each case that:
- the sub-agents were actually invoked (visible in the tool's transcript),
- `docs/` contains the 8 documents,
- the test command exits 0,
- `git log` shows one commit per milestone.

Report the outcome to the user, including anything that did not work.
