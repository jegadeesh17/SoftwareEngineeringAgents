# Native Sub-Agents for Claude Code and Antigravity — Design

**Date:** 2026-09-28
**Status:** Draft, awaiting review
**Branch:** `feat/native-subagents`

## 1. Goal

The Lead Engineering Orchestrator must be able to trigger real sub-agents
(Product Analyst, Architect, Planner, Developer, QA, Adversarial Reviewer,
DevOps) in both **Claude Code** and **Antigravity**, with **no external API
keys**. Each tool runs sub-agents on the user's own subscription.

Success looks like this: in any project folder, the user runs `/orchestrate`
(Claude Code) or `agy --agent orchestrator` (Antigravity). The orchestrator
interviews them and waits for approval. It then delegates each phase to real
sub-agents with isolated contexts. Every "pass" is backed by a test command the
orchestrator re-ran itself.

### Constraints

- No API keys, no model calls from Python.
- Both runtimes have to be generated from one source, so their prompts cannot drift.
- Installation stays non-destructive (keep files the user customized unless `--force`).

### Non-goals

- Renaming the `engine` package. That's a separate decision for the user.
- A standalone terminal pipeline. Without API keys it can't do real work.
- Parallel sub-agent execution. Delegation is sequential in this design.
- Antigravity IDE-specific UI work. Agents are discovered by the same files.

## 2. Runtime facts this design relies on

| | Claude Code | Antigravity (CLI 1.2.12 installed) |
|---|---|---|
| Workspace agents | `.claude/agents/<name>.md` | `.agents/agents/<name>/agent.md` |
| Global agents | `~/.claude/agents/<name>.md` | `~/.gemini/config/agents/<name>/agent.md` |
| Frontmatter | `name`, `description`, `tools` (comma-separated), `model` | `name`, `description`, `tools` (list), `model` (`inherit`/`flash`/`pro`), `mainAgent`, `subagent`, `commandExecutionPolicy` |
| Delegation | main session's Agent tool | `invoke_subagent` tool |
| Nesting | sub-agents cannot spawn sub-agents | up to 10 levels |
| Main-agent selection | the session itself (`/orchestrate` command) | `agy --agent <name>` or `/agents` panel |

Sources: <https://antigravity.google/docs/subagents/>, <https://antigravity.google/docs/cli/commands/agents/>.

**Unverified:** what Antigravity does when `tools` is omitted or empty. This
design always writes an explicit `tools` list, so that question never arises.
Only the tool *names* need live verification (§7).

## 3. Layout

### 3.1 Source of truth (hand-edited)

```
agents/
  roles.toml
  orchestrator.md
  product-analyst.md
  software-architect.md
  task-planner.md
  software-developer.md
  qa-tester.md
  adversarial-reviewer.md
  devops-git.md
```

Each `<role>.md` is a plain prompt body with no frontmatter. `roles.toml` holds
the metadata:

```toml
[roles.qa-tester]
description = "Writes and runs automated tests for one task; reports the exact command and exit code."
claude_tools = ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
antigravity_tools = ["view_file", "write_to_file", "replace_file_content", "grep_search", "run_command"]

[roles.orchestrator]
description = "Lead Engineering Orchestrator: interviews the user, enforces the approval gate, delegates to sub-agents, verifies results."
main_agent = true          # Antigravity: mainAgent true, subagent false; Claude Code: /orchestrate command, not an agent file
antigravity_tools = ["view_file", "write_to_file", "replace_file_content", "grep_search", "run_command", "invoke_subagent"]
```

The file is parsed with the standard-library `tomllib`, so the project gets no
new dependencies. This means `requires-python` goes from `>=3.10` to `>=3.11`.

### 3.2 Generated output (committed, never hand-edited)

Built by `python -m engine.build_agents`:

| Output | Content |
|---|---|
| `.claude/agents/<role>.md` × 7 | Frontmatter `name`, `description`, `tools: Read, Glob, ...`, `model: inherit`, then the prompt body |
| `.agents/agents/<role>/agent.md` × 7 | Frontmatter `name`, `description`, `tools: [...]`, `model: inherit`, `mainAgent: false`, `subagent: true`, then the prompt body |
| `.agents/agents/orchestrator/agent.md` | Same shape, but `mainAgent: true`, `subagent: false` |
| `templates/claude/orchestrate.md` | Slash-command frontmatter `description`, then the orchestrator body |

- Every generated file starts its body with
  `<!-- GENERATED from agents/<role>.md — edit the source and run python -m engine.build_agents -->`.
- The generator writes LF line endings.
- `--check` mode rebuilds in memory and compares against disk, after
  normalizing CRLF to LF (this repo has `core.autocrlf=true`). It exits 1 and
  lists stale files if anything differs.

### 3.3 Removed

- **The simulated pipeline:** `engine/orchestrator.py`, `engine/cli.py`,
  `engine/state.py`, `engine/observability.py`, `engine/config.py`,
  `engine/tools/`. Also `tests/test_session.py` and the `tests/test_core.py`
  tests for those modules.
- **Terminal entry points** in `pyproject.toml`: `orchestrate`, `se-agents`.
- **Role skills:** `.agents/skills/<role>/` (7 dirs). Their content moves into
  `agents/<role>.md`.
- **The Antigravity orchestrator skill:** `templates/antigravity/skills/orchestrator/`,
  replaced by the orchestrator agent.
- **Rules that restate the pipeline:** `.agents/rules/psb-workflow-discipline.md`,
  `orchestrator-governance.md`, `qa-verification.md`, `git-discipline.md`.
  Their content moves into the prompts.
- **Kept:** `.agents/rules/nomenclature-standards.md`, as the optional global rule.

### 3.4 Rewritten

- **`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`:** short guides for *developing this
  repo*. They cover the source vs. generated layout, how to regenerate, and how
  to run the tests. They no longer turn this repo's session into an orchestrator.
- **`README.md`:**
  - Usage is now `/orchestrate` or `agy --agent orchestrator` in any project.
  - Accurate architecture.
  - The old CLI and model-selection sections are removed.
- **`scripts/install_global.py`:**
  - Copies the generated files into the global directories from §2, plus
    `orchestrate.md` into `~/.claude/commands/`.
  - Keeps `--force` and `--global-rules`.
  - Drops the pip step and `--no-pip`.
  - If `~/.gemini/config/skills/orchestrator/` exists from the old install, it
    prints a notice telling the user to remove it by hand. It never deletes
    anything in the user's home directory.

## 4. Orchestrator behavior (`agents/orchestrator.md`)

The prompt is runtime-neutral. It says "delegate to the `qa-tester` sub-agent",
and each runtime maps that onto its own delegation tool.

1. **Phase 0 — Scoping** (main session, talks to the user):
   - Classify the posture (Prototype / Production) and set the M1/M2/M3 boundaries.
   - Create `docs/PROJECT_MENTAL_MODEL.md` and `docs/PROJECT_STATUS.md`.
2. **Phase 1 — Interview:**
   - Ask 3 questions: UX journey, errors and edge cases, non-goals.
   - Record the answers in the mental model.
   - **Approval gate:** stop until the user explicitly approves. Never self-approve.
3. **Planning delegation**, in sequence:
   - `product-analyst` writes `docs/SPEC.md`.
   - `software-architect` writes `docs/ARCHITECTURE.md` and `docs/DECISIONS.md`.
   - `task-planner` writes `docs/TASKS.json`.
   - After each one, the orchestrator reads the output and checks it exists and
     is non-empty before moving on.
4. **Build loop, per task in `TASKS.json` order:**
   - `software-developer` implements the task.
   - `qa-tester` writes and runs the tests, then appends
     `{task_id, command, exit_code, summary}` to `docs/QA_RESULTS.json`.
   - If the exit code is non-zero, the failure output goes back to
     `software-developer`. After 3 failed attempts the orchestrator stops and
     asks the user.
   - Before marking the task done, the orchestrator **re-runs the recorded
     command itself** and requires exit code 0.
5. **Per-milestone gate:**
   - `adversarial-reviewer` (read-only) returns a verdict with `APPROVED` or
     `REJECTED` and its findings. The orchestrator writes that into
     `docs/ADVERSARIAL_REVIEW.md`.
   - On `REJECTED`, the critical defects go back into the build loop.
   - `devops-git` commits only that milestone's files, as a Conventional Commit.
6. **Phase 4 — Handover:**
   - Final test run by the orchestrator.
   - `PROJECT_STATUS.md` fully checked.
   - Give the user the run instructions and a short engineering reflection.

**Hand-off contract:** sub-agents start with a blank context. Every delegation
prompt names:
- the task,
- the exact `docs/` files to read,
- the files the sub-agent may write,
- the output it must return.

**Living documents** (8, all in the target project's `docs/`):
`PROJECT_MENTAL_MODEL.md`, `PROJECT_STATUS.md`, `SPEC.md`, `ARCHITECTURE.md`,
`DECISIONS.md`, `TASKS.json`, `QA_RESULTS.json`, `ADVERSARIAL_REVIEW.md`.

The prompts keep the mentoring tone ("Engineering Takeaway" at each milestone),
because teaching the user is one of the project's core goals.

## 5. Tool permissions

| Role | `claude_tools` | `antigravity_tools` |
|---|---|---|
| product-analyst, software-architect, task-planner | Read, Write, Edit, Glob, Grep | view_file, write_to_file, replace_file_content, grep_search |
| software-developer, qa-tester | Read, Write, Edit, Glob, Grep, Bash | view_file, write_to_file, replace_file_content, grep_search, run_command |
| adversarial-reviewer | Read, Glob, Grep, Bash | view_file, grep_search, run_command |
| devops-git | Read, Glob, Grep, Bash | view_file, grep_search, run_command |
| orchestrator (Antigravity only) | — (main session) | view_file, write_to_file, replace_file_content, grep_search, run_command, invoke_subagent |

- The planning roles' prompts restrict their writes to `docs/`. Tool
  permissions can't enforce that restriction, so it depends on the prompt.
- `model: inherit` everywhere.
- `commandExecutionPolicy` stays at Antigravity's default (`sandbox`). See the
  §7 verification items.

## 6. Testing (pytest, TDD)

**`tests/test_build_agents.py`** (new):
- Claude output has the correct frontmatter, with `tools` as a comma-separated
  string, and a body identical to the source.
- Antigravity output has `tools` as a list and the `mainAgent`/`subagent` flags.
  The orchestrator gets `mainAgent: true` and `subagent: false`.
- The orchestrator produces no `.claude/agents/` file and does produce
  `templates/claude/orchestrate.md`.
- A role present in `roles.toml` without a prompt file raises a clear error, and
  so does the reverse.
- `--check` returns non-zero when a generated file is stale or missing, and zero
  when everything is current. Tested against a temporary tree.
- **Drift guard:** `--check` against the real repo passes, so the committed
  generated files match the source.

**`tests/test_install_global.py`** (updated):
- The agent files land in both global directories.
- Customized files are kept without `--force`.
- The global rule is only installed with `--global-rules`.
- The old orchestrator skill triggers a notice and is not deleted.

## 7. Live verification (after the tests pass)

1. **Antigravity discovery:** `agy agent` / `/agents` in a scratch folder lists
   `orchestrator` and all 7 roles.
2. **Claude Code discovery:** `/agents` lists all 7 roles, and `/orchestrate` exists.
3. **Tool names:** a short Antigravity run in which a sub-agent reads a file and
   runs `python --version`. If any tool name is rejected, fix `roles.toml` and
   regenerate.
4. **Sandbox policy:** confirm that `run_command` under the default `sandbox`
   policy can run a project's test suite. If not, set
   `commandExecutionPolicy: auto` for developer and qa-tester only.
5. **End-to-end run (needs user approval, uses their subscriptions):** a tiny
   throwaway project through `/orchestrate`, then through
   `agy --agent orchestrator`, confirming that sub-agents are actually invoked.

## 8. Risks

- **Antigravity is young.** Frontmatter fields or discovery paths may change
  between CLI versions. Mitigation: the generator is the only place that knows
  the format, so a fix is a one-file change.
- **Prompt-only restrictions.** "Write only to `docs/`" for planning roles is
  advisory. Accepted: those roles have no shell access, which limits how much
  damage they can do.
- **Claude Code orchestrator is the main session.** The user can talk it out of
  the process. Accepted: that's the human-in-the-loop design.
