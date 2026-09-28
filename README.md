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
