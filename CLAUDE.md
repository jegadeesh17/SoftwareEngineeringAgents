# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Claude Code setup (this repo)
- Hooks in `.claude/settings.json` block hand-edits to generated files (`.claude/agents/<role>.md`, `.agents/agents/<role>/agent.md`, `templates/claude/orchestrate.md`) and re-run `python -m engine.build_agents` after you edit `agents/`.
- Always edit the source in `agents/`, then run `python -m pytest -q` before finishing; the drift check fails on stale generated files.
- `.env` files are protected by a global hook. Document variables in `.env.example`.
- Commit source and generated files together, using Conventional Commits, and only when asked.
