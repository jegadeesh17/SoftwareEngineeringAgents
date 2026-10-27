# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Operating modes
- `principal_architect` is the default: the user proposes modules, data flow and seams; the architect only critiques (2-3 provocations, 2+ options, no pick); choices are recorded as an ADR in `docs/DECISIONS.md` before tasks are planned.
- Seam Lock: a `"kind": "seam"` task (interfaces, in-memory fake, contract tests) is signed off by the user, then its files are `locked_interfaces` that builders may not change.
- Split circuit breaker: tactical failures retry up to 3 times; seam failures have a retry cap of 0 and escalate to the user. The builder boundary guardrail and the reviewer's entropy audit belong to this mode too.
- Viva-Voce gate: after an APPROVED review the reviewer (still read-only) asks 2 questions, grades the user's answers and the orchestrator logs them in `docs/viva-log.md`.
- `client_delivery` is opt-in and keeps the old behavior: no proposal gate, seam lock, split breaker, entropy audit or viva. Shared sources: `agents/shared/architecture-glossary.md`, `agents/shared/candor.md`.
- Anti-sycophancy: never praise or blindly validate the user's architectural choices; be a candid peer engineer.

## Claude Code setup (this repo)
- Hooks in `.claude/settings.json` block hand-edits to generated files (`.claude/agents/<role>.md`, `.agents/agents/<role>/agent.md`, `templates/claude/orchestrate.md`) and re-run `python -m engine.build_agents` after you edit `agents/`.
- Always edit the source in `agents/`, then run `python -m pytest -q` before finishing; the drift check fails on stale generated files.
- `.env` files are protected by a global hook. Document variables in `.env.example`.
- Commit source and generated files together, using Conventional Commits, and only when asked.
