# Team retro: a self-improvement loop for the agent team

Date: 2026-10-13
Status: approved design, awaiting spec review

## Goal

Every project the team builds leaves a short, structured retrospective on the user's machine: what went well, every mistake, bug and failure, and a scored judgement of each agent. Users can contribute a retro to this repository by pull request, and the maintainer runs an LLM judge over all contributed retros to decide what to change in `agents/`.

## Decisions

| Decision | Choice | Rejected, and why |
|---|---|---|
| Where the retro lives | Central folder `~/.se-agents/retros/`, outside every project's git | Inside each project (gitignored): retros scatter across folders and vanish with them |
| Where the judging happens | Both: the orchestrator scores agents per project, and a repo-side `/judge-retros` command judges across projects | Only one side: per-project scores alone don't reveal patterns; a repo judge alone has no comparable numbers |
| Privacy | Shareable by design: retros describe the team's behavior, never the user's product | Full detail redacted on submit: redaction misses things. Private/public sections: two formats to maintain |
| Retro format | Markdown with flat `key: value` frontmatter | YAML (needs PyYAML, a new dependency); JSON (unreadable for the user) |
| Retro template location | `templates/retro.md`, installed to `~/.se-agents/retro-template.md` | Inline in the orchestrator prompt: it is at 275 of its 300-line budget, and includes count toward it |
| Who writes the retro | Only the orchestrator | Sub-agents writing too: they start blank, can't see retries or UAT, and would need write access outside the project |
| Version stamp | Installer writes `~/.se-agents/source.json` | Adding keys to `installed.json`: it is a flat path-to-hash map and the installer's update logic depends on that |

## Components

### 1. Retro template: `templates/retro.md` (new, source)

Installed by `scripts/install_global.py` to `~/.se-agents/retro-template.md` through the existing `install_text` (manifest-tracked, user edits kept unless `--force`).

Frontmatter (flat, all keys required, `key: value` per line between `---` lines):

| Key | Values |
|---|---|
| `retro_format` | `1` |
| `sea_commit` | short commit from `source.json`, or `unknown` |
| `runtime` | `claude-code` or `antigravity` |
| `orchestrator_model` | the model the orchestrator ran on, e.g. `opus` |
| `started` | `YYYY-MM-DD` |
| `finished` | `YYYY-MM-DD`, or empty while in progress |
| `project_type` | generic description, e.g. `Streamlit dashboard`; never a product name |
| `existing_code`, `ui`, `sensitive_data`, `deploy` | `yes` or `no` |
| `change_type` | `new`, `Feature`, `Fix`, `Refactor`, `Redesign` or `Transformation` |
| `milestones_planned`, `milestones_accepted` | integers |
| `outcome` | `completed`, `abandoned` or `in-progress` |

Body, three required sections in this order:

- `## Summary`: written at handover. What went well, the top 3 recurring problems, and up to 5 ranked suggested changes to the team, each naming the role prompt or workflow step to change.
- `## Scores`: table `| Agent | Correctness | Instructions | First try | Hand-off | Evidence |`. One row per agent that ran, the orchestrator included. Each score is `1`–`5` or `n/a`. Evidence cites log rows or counts.
- `## Log`: table `| Date | Phase/task | Agent | Kind | Severity | What happened | Cost | Likely cause | Suggested change |`.
  - Kind: `went-well`, `mistake`, `bug`, `failure`, `user-correction`, `hand-off-gap`, `environment`, `conflict`.
  - Severity: `low`, `medium`, `high` (`went-well` rows use `-`).
  - Cost: retries, rework or time, e.g. `2 retries`.

The template carries the scoring rubric as anchored counts, so the judge scores evidence rather than impressions:

- **First try:** 5 = every task passed the orchestrator's first verification; 3 = some tasks needed a retry; 1 = a task hit the retry limit.
- **Correctness:** 5 = no rejected review and no UAT defect traced to the agent; 3 = one rejection or defect; 1 = repeated rejections or a defect that reached the user twice.
- **Instructions:** 5 = no logged deviation; 3 = one deviation (wrong file, skipped step, out-of-scope change); 1 = repeated deviations.
- **Hand-off:** 5 = no `hand-off-gap` caused by or blocking the agent; 3 = one; 1 = repeated.

### 2. Installer: `scripts/install_global.py`

- Installs `templates/retro.md` to `~/.se-agents/retro-template.md`.
- Writes `~/.se-agents/source.json`: `{"repo": "<absolute path of this clone>", "commit": "<git rev-parse --short HEAD, or unknown>"}`. It is always overwritten, since it describes the current install and is not user-editable.
- `installed.json` format is unchanged.

### 3. Orchestrator: `agents/orchestrator.md` (about 15 added lines, budget stays 300)

- **Principles:** one bullet: *Learn from every build*. Log the team's behavior as it happens, good and bad (see "Team retro").
- **Phase 0:** after the repository exists:
  1. Read `~/.se-agents/source.json` and `~/.se-agents/retro-template.md`. Resolve the home directory with `python -c "import pathlib; print(pathlib.Path.home())"`.
  2. Create `~/.se-agents/retros/<project-folder>-<YYYY-MM-DD>.md` from the template (`-2`, `-3` on collision), with the frontmatter filled and `outcome: in-progress`.
  3. Record the path in `docs/PROJECT_MENTAL_MODEL.md` in its `~` form.
  4. If `source.json` is missing, use `sea_commit: unknown`. If the template is missing, ask the user to run `python scripts/install_global.py` in their SoftwareEngineeringAgents folder; if they decline, carry on without a retro. (The template is the only copy of the format, and the prompt has no room to repeat it.)
- **Resuming:** append to the retro recorded in `docs/PROJECT_MENTAL_MODEL.md`.
- **Milestone approval (Phase 3 step 11):** self-check. Add any event from this milestone that is not yet logged, then update `milestones_accepted`.
- **Phase 4 (new step before the final message):** write `## Summary` and `## Scores`, then set `finished` and `outcome`. Tell the user the retro's path and the contribute command `python <repo>/scripts/contribute_retro.py`, with `<repo>` taken from `source.json`.
- **New section "Team retro"** containing:
  - **When to log, immediately and one row per event:**
    - a task passing first verification (`went-well`, batched as one row per milestone);
    - a retry, with its root cause;
    - a sub-agent claiming success that the orchestrator's own run disproved;
    - a REJECTED review;
    - a defect the user found at prototype review or UAT;
    - the user correcting or overriding the orchestrator;
    - a sub-agent missing information that `docs/` lacked, or acting outside its role or files;
    - a tool, permission or environment failure;
    - a conflict between agents;
    - anything that worked notably well.
  - **Writing rules:**
    - Describe the team's behavior, not the product.
    - No product or client names, code, absolute paths, URLs, emails, secrets or `.env` values.
    - "Likely cause" names a role prompt (`backend-developer`) or a workflow step (`Phase 2.4`).
    - Scores follow the template's rubric and cite evidence. Score yourself by the same rubric.
  - **Never commit the retro.** It lives outside the project.
  - **Fallback:** if the central folder cannot be written (for example, the runtime refuses paths outside the workspace), write `.se-agents/RETRO.md` in the project, add `.se-agents/` to `.gitignore`, and tell the user.
- **Living documents:** one line noting the retro lives outside the project and is never committed.

### 4. Validation module: `engine/retros.py` (new)

Pure functions with no I/O beyond the text passed in. Used by the contribute script and the tests.

- `parse(text) -> (frontmatter: dict, body: str)`
- `validate(text) -> list[str]`: errors for missing or unknown keys, bad enum values, bad dates or integers, and missing or misordered sections. It also checks each Scores row (`1`–`5` or `n/a`) and each Log row's Kind and Severity.
- `python -m engine.retros FILE_OR_FOLDER...`: a CLI that validates and privacy-scans files (a folder means its `*.md`), exiting 1 on any problem. `/judge-retros` and maintainers use it.
- `privacy_findings(text, usernames: list[str]) -> list[str]`. It flags:
  - Windows or POSIX absolute paths (`X:\`, `/Users/`, `/home/`);
  - email addresses;
  - key-like strings (`sk-`, `ghp_`, `github_pat_`, `AKIA`, and hex or base64 runs of 32+ characters);
  - URLs other than this repository's GitHub URL;
  - any of the given usernames as a whole word.

### 5. Contribute script: `scripts/contribute_retro.py` (new)

`python scripts/contribute_retro.py [PATH] [--dry-run]`

1. With no `PATH`, list `~/.se-agents/retros/*.md` numbered (newest first) and ask which to contribute.
2. Run `validate` and `privacy_findings` (usernames: the current login name and the home folder name). On any finding, print each with its line number and exit 1 without touching git. The user edits the file and re-runs. There is no override flag.
3. Pick the target name `retros/community/<started>-<project_type slug>-<6 random hex>.md`. With `--dry-run`, print it and exit 0.
4. Require a clean working tree in this clone. Create branch `retro/<target stem>`, copy the file, then commit with `docs(retros): add <target stem>`.
5. Ask `Open a pull request now? [y/N]`.
   - On `y`, run `gh pr create --fill`. gh pushes the branch and offers to fork when the user cannot push to the repository.
   - On anything else, print the command to run later.
6. Switch back to the branch the user started on.

### 6. Community folder: `retros/` (new)

- `retros/README.md`: what retros are, the privacy rules, and how to contribute with the script.
- `retros/community/`: contributed retros (kept in git with a `.gitkeep`).
- `retros/REPORT.md`: written by `/judge-retros`. The maintainer decides whether to commit it.

### 7. Repo-side judge: `.claude/commands/judge-retros.md` (new, maintainer only, not installed)

Frontmatter: `description`, `model: opus`, `effort: high`. Argument: a folder of retros, default `retros/community/` (the maintainer can pass `~/.se-agents/retros/` to judge their own local retros). The command must:

1. Run `python -m engine.retros <folder>`. Judge only the retros it reports OK, and list the others with their problems.
2. Aggregate scores per agent: the mean and count per criterion, split by `runtime`.
3. Cluster problem rows by agent, kind and likely cause. Rank clusters by the number of distinct retros × severity weight (low 1, medium 2, high 3).
4. For each cluster, compare the oldest `sea_commit` it appears in with the current source. Read the role prompt it names and run `git log <commit>..HEAD -- agents/` to mark it `open` or `likely fixed (<commit>)`.
5. Collect recurring `went-well` rows into a "Preserve" list, so fixes don't regress what works.
6. Write `retros/REPORT.md` with:
   - a header (retro count, date range, commits covered);
   - the score table;
   - the ranked clusters, each with its evidence (retro file and log row), its status and one concrete proposed edit (the file under `agents/` and the exact change);
   - the Preserve list.
7. Never edit `agents/` or `roles.toml`. The maintainer applies changes through the normal "Changing the team" steps.

### 8. Docs

- **`README.md`:**
  - a row in "What makes it different": *The team never learns from its mistakes* → **Self-retro**;
  - a short "Retros and contributing" section: where the file is, what is in it, how to contribute it;
  - in "Engineering decisions", one bullet on the judge loop.
- **`AGENTS.md`:**
  - layout rows for `templates/retro.md`, `engine/retros.py`, `scripts/contribute_retro.py`, `retros/` and `.claude/commands/judge-retros.md`;
  - a step 0 in "Changing the team": run `/judge-retros` and start from `retros/REPORT.md`.

## Testing

- **`tests/test_build_agents.py`:** the orchestrator prompt contains `~/.se-agents/retros/`, `retro-template.md`, `source.json`, the `.se-agents/RETRO.md` fallback and the contribute command. The existing 300-line budget test still passes.
- **`tests/test_install_global.py`:**
  - `retro-template.md` is installed and manifest-tracked, and user edits are kept;
  - `source.json` has `repo` and `commit` (`unknown` when git is unavailable);
  - `installed.json` stays a flat map.
- **`tests/test_retros.py`:**
  - `validate` passes a filled sample and fails on a missing key, a bad enum, a bad date and a missing section;
  - `privacy_findings` flags each pattern and passes a clean sample;
  - the contribute script's `--dry-run` blocks a retro with a finding (exit 1) and prints an anonymous target name for a clean one;
  - every file in `retros/community/*.md` passes `validate` and `privacy_findings`, so CI rejects unsafe contributions.
- `templates/retro.md` with placeholder values filled passes `validate`.

## Out of scope

- Automatic upload or telemetry: sharing always needs the user's y/N and a pull request.
- Sub-agents writing to the retro.
- Auto-applying the judge's proposed edits.
- Dashboards or charts of scores.
- Changing any sub-agent prompt.

## Risks

- **Antigravity may refuse writes outside the workspace.** This is unverified; the fallback covers it, and it will be checked live on the first Antigravity build.
- **Claude Code prompts for permission** on the first write outside the project in each session. The README tells users they can allow `~/.se-agents/**`.
- **Self-scoring bias:** the orchestrator judges itself. The count-anchored rubric and required evidence limit it, and the repo-side judge sees many projects.
- **Prompt adherence:** logging is an instruction, not enforced. The milestone self-check and the Phase 4 summary are the safety nets.
