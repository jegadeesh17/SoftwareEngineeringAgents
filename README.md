# SoftwareEngineeringAgents

> An AI software engineering team for non-technical builders ("vibe coders"). It runs natively inside **Claude Code** and **Google Antigravity** and needs no API keys.

You talk to one **Lead Engineering Orchestrator**. It interviews you and waits for your approval. Then it delegates the work to specialist sub-agents, each with its own context and tool permissions, and checks every result by running the tests itself. Along the way it explains *why* professional teams work this way.

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
# from a clone of this repository
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

## Customize the team

The prompts live in `agents/`. See [AGENTS.md](AGENTS.md) for how to edit and regenerate them.

## Limitations

- In Claude Code, sub-agents cannot start other sub-agents, so the orchestrator is your main session. It follows the process because its instructions say so, and you can talk it out of it.
- "Planning agents only write to `docs/`" is an instruction, not a hard limit. Those agents have no shell access.
- Antigravity's custom-agent format is new. If it changes, only `engine/build_agents.py` needs updating.

## License

MIT (see [LICENSE](LICENSE)).
