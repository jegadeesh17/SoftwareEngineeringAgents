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
