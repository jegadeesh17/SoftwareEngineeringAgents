# SoftwareEngineeringAgents

[![CI](https://github.com/jegadeesh17/SoftwareEngineeringAgents/actions/workflows/ci.yml/badge.svg)](https://github.com/jegadeesh17/SoftwareEngineeringAgents/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)

> An AI software engineering team that runs inside **Claude Code** and **Google Antigravity**. It interviews you, waits for your approval, then plans, builds, tests and reviews your project with specialist sub-agents. No API keys: it runs on the subscription you already have.

It is built for engineers by default (`principal_architect` mode: you own and defend the architecture), with a `client_delivery` mode for non-technical builders ("vibe coders"). It explains *why* professional teams work this way while it builds.

## What makes it different

AI coding agents tend to fail in predictable ways. Each one has a specific guard here:

| Failure | Guard |
|---|---|
| Builds the wrong thing | **Approval gate.** The orchestrator interviews you and stops until you approve the scope. It never approves on your behalf. |
| Says "tests pass" without proof | **Verify, don't trust.** A task is done only when the orchestrator re-runs the recorded test command itself and sees exit code 0. |
| Loops forever on a failing fix | **Bounded retries.** A tactical failure (syntax, typo, logic inside one module) goes back to the developer up to 3 times, then the orchestrator asks you. |
| The AI invents the architecture for you | **Architecture proposal gate.** You sketch the deep modules, data flow and seams first. The architect only critiques, with 2-3 provocations and at least 2 options each, and never picks. Your choices are recorded as an ADR before any task is planned. |
| Design failures hide inside retries | **Split circuit breaker.** A seam or contract failure gets 0 retries and goes straight to you. Interfaces are locked (Seam Lock) before implementation, and builders cannot edit them. |
| You cannot explain the code that was built | **Viva-voce gate.** After the milestone review passes, the reviewer asks you 2 technical questions about the code and grades your typed answers. The milestone is not complete until you can explain it. |
| Nobody checks the work | **Adversarial review.** A read-only reviewer audits every milestone and returns APPROVED or REJECTED. |
| Security is an afterthought | **Security review at two points.** For projects that handle personal, health, payment or credential data, a read-only security reviewer checks the architecture's security section before any task is planned, then audits each milestone for authorization gaps, injection and leaked secrets. |
| Agents can do too much | **Least privilege.** Each role gets only the tools it needs: planners have no shell, and the reviewer cannot edit files. |
| Context is lost between sessions | **Files are the hand-off.** The living documents in `docs/` hold the plan, decisions, test results and status, so any agent (or you) can resume. |
| Agents approve what you would reject | **You accept, not the agents.** For a UI, you click through a prototype before the architecture is frozen, and you test every milestone yourself before it counts as done. Feedback is sorted into UI, Behavior or Contract, and only Contract changes touch the architecture. |
| Generic, "AI-looking" UI | **Built-in design standard.** The frontend developer and UI reviewer carry their own UI craft rules and a refuse list of AI-looking patterns, and preload the [Impeccable](https://impeccable.style) skill on top when it is installed. Screenshots are reviewed at desktop and mobile widths. |
| Breaks code it didn't write | **Existing-project mode.** A codebase analyst maps the stack, conventions and a baseline test run first. Work happens on its own branch, and the reviewer checks for regressions against the starting commit. |
| Multi-agent runs burn through tokens | **Lean by design.** Agents read only the doc sections their task names, keep command output short, and the per-task loop uses one agent instead of two. Small changes skip the planning pipeline (never the tests, reviews or your sign-off), and the orchestrator suggests a fresh session every few tasks. |
| The team never learns from its mistakes | **Self-retro.** Each build leaves a retro in `~/.se-agents/retros/`, outside the project's git: what went well, every mistake, bug and failure, a score for each agent backed by evidence, and measured token use per agent. `/judge-retros` turns your retros into ranked fixes to the team, and flags any drop in quality. |

## How it works

```
You <──> ORCHESTRATOR (the only agent that talks to you)
          1. Interviews you: vision, project name, prototype vs production
          2. Sets up the repo first, itself: new GitHub repo, existing URL, or local only
          │         (existing code: a working branch instead)
          │     └─> codebase-analyst ──> docs/CODEBASE_MAP.md + baseline test run
          │         (existing code only)
          3. Interviews you: UX, errors, non-goals
          4. STOPS: "Do you approve this scope?"  <- nothing is built without your yes
          │     principal_architect: YOU propose modules, data flow and seams ("you decide" is refused),
          │     architect critiques with provocations, you choose and justify -> ADR in docs/DECISIONS.md
          │     └─> ui-reviewer ───────> "before" screenshots (existing UI only)
          │
          ├─> product-analyst ────────> docs/SPEC.md
          ├─> software-architect ─────> docs/ARCHITECTURE.md (draft), docs/DECISIONS.md
          ├─> design studio (UI only) ─> direction interview with you (Impeccable `shape` if installed) -> PRODUCT.md
          ├─> frontend-developer ─────> clickable prototype; you review it, feedback -> docs/FEEDBACK.md
          ├─> software-architect ─────> architecture FROZEN; you sign off what is expensive to change
          ├─> security-reviewer ──────> reviews the design's security section (sensitive-data only)
          ├─> task-planner ───────────> docs/TASKS.json (M1 MVP -> M2 Core -> M3 Polish)
          │
          5. Setup: checks your tools, lists the accounts and API keys the plan
             needs (with cost), writes .env.example
          6. Walkthrough: docs/WALKTHROUGH.md shows how the app works for you,
             the architecture diagram and the milestone plan
             STOPS: "Does this match what you want?"  <- no code before your yes
             then you fill in .env yourself
          │
          │   for each task:
          ├─> backend-developer / frontend-developer / platform-engineer ──> tests first, then the code,
          │     runs the fast tests (with lint and type checks) -> docs/QA_RESULTS.json
          │     seam task first -> YOU sign off the interfaces (Seam Lock)
          │     tactical fail -> back to the developer (up to 3 tries, then it asks you)
          │     seam fail -> 0 retries, escalated to you
          │     pass -> the orchestrator re-runs the recorded command itself, then commits and
          │             pushes that task
          │
          │   for each milestone:
          ├─> qa-tester ──────────────> tests for uncovered criteria and cross-task wiring, full suite
          ├─> adversarial-reviewer ───> read-only audit + entropy check -> APPROVED or REJECTED
          ├─> viva-voce (principal_architect) ─> 2 questions, YOU answer, graded until PASS -> docs/viva-log.md
          ├─> security-reviewer ──────> read-only security audit (sensitive-data only)
          ├─> ui-reviewer (UI only) ──> screenshots + UI craft audit -> APPROVED or REJECTED
          └─> YOU test it (UAT) ──────> feedback triaged and fixed until you accept the milestone
```

## The team

| Agent | Produces | Can change files? |
|---|---|---|
| Orchestrator | the interview, approvals, setup, status tracking | docs, `.gitignore` and `.env.example` only (by instruction); runs the tests and makes all the git commits |
| CodebaseAnalyst | `docs/CODEBASE_MAP.md` (existing projects only) | docs only, and can run the project's tests |
| ProductAnalyst | `docs/SPEC.md` | docs only |
| SoftwareArchitect | `docs/ARCHITECTURE.md`, `docs/DECISIONS.md` | docs only |
| TaskPlanner | `docs/TASKS.json` | docs only |
| BackendDeveloper | the non-UI code and its tests | yes, and can run commands |
| FrontendDeveloper | the prototype, UI code and its tests (UI projects only) | yes, can run commands and use the built-in UI craft standard (and Impeccable, if installed) |
| QaTester | once per milestone: tests for uncovered criteria and cross-task wiring, a full test run in `docs/QA_RESULTS.json` | tests and docs, and can run commands |
| AdversarialReviewer | APPROVED/REJECTED verdict, architectural entropy audit, viva questions and grading (`principal_architect`) | **no**: read-only, can run tests |
| UiReviewer | screenshots and an APPROVED/REJECTED verdict (UI projects only) | **no**: read-only, writes only screenshots under `.ui-review/` |
| PlatformEngineer | CI, container and deploy config, `docs/DEPLOYMENT.md` (deploy projects only) | yes, can run commands; never deploys |
| SecurityReviewer | APPROVED/REJECTED verdict on the design and on each milestone (sensitive-data projects only) | **no**: read-only |

## Install

Requirements: Python 3.11+ (for the installer only), plus Claude Code and/or the Antigravity CLI.

```bash
git clone https://github.com/jegadeesh17/SoftwareEngineeringAgents.git
cd SoftwareEngineeringAgents
python scripts/install_global.py
```

This installs:
- `~/.claude/agents/*.md`: the 11 Claude Code sub-agents.
- `~/.claude/commands/orchestrate.md`: the `/orchestrate` command.
- `~/.gemini/config/agents/*/agent.md`: the orchestrator and 11 sub-agents for Antigravity.
- `~/.se-agents/retro-template.md`, `doc-templates.md`, `usage.py` and `source.json`: the retro format, the document templates the orchestrator reads on demand, the token usage report, and which version of the team you installed.

The installer records what it wrote in `~/.se-agents/installed.json`. Re-running it after `git pull` updates files it installed before and keeps any you've edited. It exits with an error if it had to skip a file.

Options:
- `--force` overwrites files you've customized. Without it they are kept.
- `--global-rules` also installs an always-on naming-convention rule for every Antigravity project.

## Use

Open an empty folder for a new project, or the folder of an existing one, then:

- **Claude Code:** run `claude --model opus --effort high` and type `/orchestrate`. The command switches to Opus at high effort only for the turn you type it, so start the session on it; otherwise the orchestrator asks you to restart.
- **Antigravity:** run `agy --agent orchestrator`, or pick `orchestrator` in `/agents`.

**Modes.** `principal_architect` is the default. Type `/orchestrate client_delivery` (or tell the orchestrator) for the old hands-off flow: no architecture proposal, seam lock, split breaker, entropy audit or viva. For an existing project, say "deepen" to have the architect find 3-5 shallow modules to consolidate.

**Existing project.** The orchestrator detects code in the folder and switches mode. It asks what kind of change it is (`Feature`, `Fix`, `Refactor`, `Redesign` or `Transformation`, see below) instead of for a product vision, and it won't start with uncommitted changes in the tree. It creates a working branch and never commits to `main`. The codebase analyst then maps the stack, conventions and a baseline test run, and the team follows the project's own style and test runner. If the baseline is red, the orchestrator asks whether to fix it first or accept the named failures. It plans one to three milestones sized to the change, and at handover it points you to the branch to open a pull request from.

The orchestrator asks where the code should live (a new GitHub repository needs the [GitHub CLI](https://cli.github.com/) logged in with `gh auth login`). After the plan is approved, it tells you which accounts and API keys the project needs; you put them in `.env` yourself and never paste them into the chat.

At the end you have working code, passing tests, one git commit per verified task (pushed to GitHub if you chose it), and the living documents in `docs/` explaining what was built and why. Some appear only when they apply: a codebase map for an existing project, a UI review for a UI, a security review for a project with sensitive data, and a deployment runbook when you will deploy.

## Changing an existing project

The orchestrator asks which kind of change it is, and every agent follows the same label:

| Change type | What it is | How the team treats it |
|---|---|---|
| `Feature`, `Fix`, `Refactor` | A change to the existing code | Extend what exists, keep its stack and style, check for regressions |
| `Redesign` | A new look and UX, same behavior and backend | "Before" screenshots first; screens convert one at a time; you compare before and after; behavior parity is checked |
| `Transformation` | A stack or architecture migration | Characterization tests pin today's behavior first; old and new run side by side while journeys migrate one at a time; deleting old code needs your explicit yes |

## Retros: help the team improve

Every build leaves a short retro on your machine, in `~/.se-agents/retros/<project>-<date>.md`, outside the project and its git. The orchestrator logs what went well and every mistake, bug and failure as it happens. At handover it scores each agent against a fixed rubric, citing evidence. The retro describes the team's behavior, never your product: no names, code, paths or secrets.

In Claude Code the first write outside the project asks for permission. Approve it, or add `"Edit(~/.se-agents/**)"` to `permissions.allow` in `~/.claude/settings.json`.

At each milestone the orchestrator also fills the retro's `## Usage` table with measured token use per agent (runs, turns, average and peak context), read from Claude Code's own session transcripts by `~/.se-agents/usage.py`. You can run it yourself on any project: `python ~/.se-agents/usage.py <project folder>`.

To learn from your retros, open Claude Code in your clone and run `/judge-retros`. It validates every retro in `~/.se-agents/retros/`, clusters recurring problems and cost hot spots, ranks any drop in quality after a change to the agents first, checks whether a later commit already fixed each problem, and writes `retros/REPORT.md` with concrete edits to the agents. You decide what to change.

## Engineering decisions

- **The first version was thrown away.** It was a Python pipeline that simulated the agents. Without API keys it could not do real work, so it was removed ([`3f4f24f`](https://github.com/jegadeesh17/SoftwareEngineeringAgents/commit/3f4f24f)) in favor of each tool's native sub-agents. The design is in [docs/superpowers/specs](docs/superpowers/specs/2026-09-28-native-subagents-design.md).
- **One source, two runtimes.** Each role is defined once in `agents/`. [`engine/build_agents.py`](engine/build_agents.py) renders it into the Claude Code and Antigravity formats, so the two cannot drift apart. `--check` fails CI if a generated file is stale, and Claude Code hooks in this repo block hand-edits to generated files.
- **Model tiering.** Each role runs on the model Anthropic positions for its kind of work. Opus handles judgment: the orchestrator (at high effort), product analyst, architect, task planner, adversarial reviewer and security reviewer. Sonnet handles coding and visual review: the backend and frontend developers and the UI reviewer. Haiku handles read-heavy or downstream-verified work: the codebase analyst, QA tester and platform engineer. Each role's reasoning effort is pinned too. The orchestrator does the git work itself, since a sub-agent for a few git commands only adds waiting. A role's model and effort are one line each in [`agents/roles.toml`](agents/roles.toml). Antigravity agents use your session's model.
- **Checked live, not assumed.** Antigravity enforces each agent's `tools` list. This was confirmed with CLI 1.2.12 by trying to call tools outside the list.
- **A non-destructive installer.** It keeps a manifest of what it wrote, updates only its own files on reinstall, and never overwrites your edits without `--force`.
- **The team judges itself.** Each retro scores every agent against a rubric anchored to counts (retries, rejected reviews, UAT defects), so an LLM judge scores evidence, not impressions, and records measured token use per agent. A repo-side judge clusters problems and cost across retros, checks whether a later commit already fixed them, and proposes edits that a person applies.
- **Lean context, same gates.** A real build of an 87k-line app spent most of its tokens re-sending context, not writing code: whole design docs re-read by each agent, a long-running orchestrator session, and two agents per task. The team now follows practices published by Anthropic, OpenAI and Cognition: just-in-time section reads, short tool output, state kept in files instead of a growing context, single-writer tasks with context-free reviewers, lint in the fast test loop, and effort scaled to the change's size. Every verification gate is kept, and a test fails if one is removed.
- **Tested.** pytest covers the generator, the installer and the rule format, including a drift check against the committed files. CI runs on Linux and Windows with Python 3.11 and 3.13.

## Fork it and make it yours

This is a personal project, open-sourced so you can build your own team on it. Fork it rather than waiting on issues.

1. Edit a role's metadata (description, tools, model, effort) in `agents/roles.toml`, or its prompt in `agents/<role>.md`.
2. Regenerate: `python -m engine.build_agents`
3. Test: `python -m pytest -q` (dev dependencies: `pip install -e ".[dev]"`)
4. Install your version: `python scripts/install_global.py`

[AGENTS.md](AGENTS.md) is the full developer guide.

## Limitations

- In Claude Code, sub-agents cannot start other sub-agents, so the orchestrator is your main session. It follows the process because its instructions say so, and you can talk it out of it.
- "Planning agents only write to `docs/`" is an instruction, not a hard limit. Those agents have no shell access.
- Existing-project mode is prompt-level and has not been exercised against a real project yet. It never touches a `docs/` file you already have under one of the team's names: it asks you to move it first.
- Projects with a UI need Playwright with Chromium. The [Impeccable](https://impeccable.style) plugin is optional: the UI agents work without it and use it on top when installed (Claude Code only).
- The security reviewer and platform engineer run only when the orchestrator records `sensitive-data` or `deploy` as yes in Phase 0, and they have not been exercised against a real project yet. The platform engineer prepares CI, containers and a deploy runbook but never deploys: that stays your decision.
- Antigravity's custom-agent format is new. If it changes, only `engine/build_agents.py` needs updating.

## License

MIT (see [LICENSE](LICENSE)). Built by [Jegadeesh](https://github.com/jegadeesh17).
