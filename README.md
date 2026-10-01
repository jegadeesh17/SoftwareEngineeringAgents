# SoftwareEngineeringAgents

[![CI](https://github.com/jegadeesh17/SoftwareEngineeringAgents/actions/workflows/ci.yml/badge.svg)](https://github.com/jegadeesh17/SoftwareEngineeringAgents/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)

> An AI software engineering team that runs inside **Claude Code** and **Google Antigravity**. It interviews you, waits for your approval, then plans, builds, tests and reviews your project with specialist sub-agents. No API keys: it runs on the subscription you already have.

It is built for non-technical builders ("vibe coders"), and it explains *why* professional teams work this way while it builds.

## What makes it different

AI coding agents tend to fail in predictable ways. Each one has a specific guard here:

| Failure | Guard |
|---|---|
| Builds the wrong thing | **Approval gate.** The orchestrator interviews you and stops until you approve the scope. It never approves on your behalf. |
| Says "tests pass" without proof | **Verify, don't trust.** A task is done only when the orchestrator re-runs the recorded test command itself and sees exit code 0. |
| Loops forever on a failing fix | **Bounded retries.** A failing task goes back to the developer up to 3 times, then the orchestrator asks you. |
| Nobody checks the work | **Adversarial review.** A read-only reviewer audits every milestone and returns APPROVED or REJECTED. |
| Agents can do too much | **Least privilege.** Each role gets only the tools it needs: planners have no shell, and the reviewer cannot edit files. |
| Context is lost between sessions | **Files are the hand-off.** Eight living documents in `docs/` hold the plan, decisions, test results and status, so any agent (or you) can resume. |

## How it works

```
You <──> ORCHESTRATOR (the only agent that talks to you)
          1. Interviews you: vision, project name, prototype vs production
          2. Sets up the repo first: new GitHub repo, existing URL, or local only
          │     └─> devops-git ────────> git init, remote, first commit
          3. Interviews you: UX, errors, non-goals
          4. STOPS: "Do you approve this scope?"  <- nothing is built without your yes
          │
          ├─> product-analyst ────────> docs/SPEC.md
          ├─> software-architect ─────> docs/ARCHITECTURE.md, docs/DECISIONS.md
          ├─> task-planner ───────────> docs/TASKS.json (M1 MVP -> M2 Core -> M3 Polish)
          │
          5. Setup: checks your tools, lists the accounts and API keys the plan
             needs (with cost), writes .env.example; you fill in .env yourself
          │
          │   for each task:
          ├─> software-developer ─────> writes the code
          ├─> qa-tester ──────────────> writes and runs tests -> docs/QA_RESULTS.json
          │     fail -> back to the developer (up to 3 tries, then it asks you)
          │     pass -> the orchestrator re-runs the fast tests itself, then commits and
          │             pushes that task (full suite once per milestone)
          │
          │   for each milestone:
          └─> adversarial-reviewer ───> read-only audit -> APPROVED or REJECTED
```

## The team

| Agent | Produces | Can change files? |
|---|---|---|
| Orchestrator | the interview, approvals, setup, status tracking | docs, `.gitignore` and `.env.example` only (by instruction); runs the tests and makes the per-task commits |
| Product Analyst | `docs/SPEC.md` | docs only |
| Software Architect | `docs/ARCHITECTURE.md`, `docs/DECISIONS.md` | docs only |
| Task Planner | `docs/TASKS.json` | docs only |
| Software Developer | the code | yes, and can run commands |
| QA Tester | tests and `docs/QA_RESULTS.json` | tests and docs, and can run commands |
| Adversarial Reviewer | APPROVED/REJECTED verdict | **no**: read-only, can run tests |
| DevOps & Git | the repo and remote, phase and milestone commits | no: sets up the repo, stages, commits and pushes only |

## Install

Requirements: Python 3.11+ (for the installer only), plus Claude Code and/or the Antigravity CLI.

```bash
git clone https://github.com/jegadeesh17/SoftwareEngineeringAgents.git
cd SoftwareEngineeringAgents
python scripts/install_global.py
```

This installs:
- `~/.claude/agents/*.md`: the 7 Claude Code sub-agents.
- `~/.claude/commands/orchestrate.md`: the `/orchestrate` command.
- `~/.gemini/config/agents/*/agent.md`: the orchestrator and 7 sub-agents for Antigravity.

The installer records what it wrote in `~/.se-agents/installed.json`. Re-running it after `git pull` updates files it installed before and keeps any you've edited. It exits with an error if it had to skip a file.

Options:
- `--force` overwrites files you've customized. Without it they are kept.
- `--global-rules` also installs an always-on naming-convention rule for every Antigravity project.

## Use

Open an empty folder for your new project, then:

- **Claude Code:** run `claude` and type `/orchestrate`.
- **Antigravity:** run `agy --agent orchestrator`, or pick `orchestrator` in `/agents`.

The orchestrator asks where the code should live (a new GitHub repository needs the [GitHub CLI](https://cli.github.com/) logged in with `gh auth login`). After the plan is approved, it tells you which accounts and API keys the project needs; you put them in `.env` yourself and never paste them into the chat.

At the end you have working code, passing tests, one git commit per verified task (pushed to GitHub if you chose it), and eight documents in `docs/` explaining what was built and why.

## Engineering decisions

- **The first version was thrown away.** It was a Python pipeline that simulated the agents. Without API keys it could not do real work, so it was removed ([`3f4f24f`](https://github.com/jegadeesh17/SoftwareEngineeringAgents/commit/3f4f24f)) in favor of each tool's native sub-agents. The design is in [docs/superpowers/specs](docs/superpowers/specs/2026-09-28-native-subagents-design.md).
- **One source, two runtimes.** Each role is defined once in `agents/`. [`engine/build_agents.py`](engine/build_agents.py) renders it into the Claude Code and Antigravity formats, so the two cannot drift apart. `--check` fails CI if a generated file is stale, and Claude Code hooks in this repo block hand-edits to generated files.
- **Model tiering.** Judgment-heavy roles (architect, developer, reviewer) inherit your session's model. Routine roles use cheaper ones: Sonnet for the analyst, planner and QA, Haiku for git. Each role's model is one line in [`agents/roles.toml`](agents/roles.toml).
- **Checked live, not assumed.** Antigravity enforces each agent's `tools` list. This was confirmed with CLI 1.2.12 by trying to call tools outside the list.
- **A non-destructive installer.** It keeps a manifest of what it wrote, updates only its own files on reinstall, and never overwrites your edits without `--force`.
- **Tested.** pytest covers the generator, the installer and the rule format, including a drift check against the committed files. CI runs on Linux and Windows with Python 3.11 and 3.13.

## Fork it and make it yours

This is a personal project, open-sourced so you can build your own team on it. Fork it rather than waiting on issues.

1. Edit a role's metadata (description, tools, model) in `agents/roles.toml`, or its prompt in `agents/<role>.md`.
2. Regenerate: `python -m engine.build_agents`
3. Test: `python -m pytest -q` (dev dependencies: `pip install -e ".[dev]"`)
4. Install your version: `python scripts/install_global.py`

[AGENTS.md](AGENTS.md) is the full developer guide.

## Limitations

- In Claude Code, sub-agents cannot start other sub-agents, so the orchestrator is your main session. It follows the process because its instructions say so, and you can talk it out of it.
- "Planning agents only write to `docs/`" is an instruction, not a hard limit. Those agents have no shell access.
- Antigravity's custom-agent format is new. If it changes, only `engine/build_agents.py` needs updating.

## License

MIT (see [LICENSE](LICENSE)). Built by [Jegadeesh](https://github.com/jegadeesh17).
