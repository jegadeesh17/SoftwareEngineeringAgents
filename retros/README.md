# Team retros

Every project the team builds leaves a retro on the builder's machine, in `~/.sea/retros/`: what went well and every mistake, bug and failure, logged as facts only. Older retros may also carry the orchestrator's own scores and a `## Usage` table. Retros describe the team's behavior, never the product: no product or client names, code, paths, URLs, emails or secrets.

## How retros are used

Run `/judge-retros` in Claude Code in this repository. It reads every retro in `~/.sea/retros/` (or a folder you name), scores each agent itself from the logs and the project's test and review records, backfills token usage per agent with `engine/usage.py`, clusters recurring problems and cost hot spots, flags any drop in quality after a change to the agents, checks whether a later commit already fixed each problem, and writes `REPORT.md` with ranked, concrete changes to the agents. A person decides what to change, through "Changing the team" in `AGENTS.md`.
