# Team retros

Every project the team builds leaves a retro on the builder's machine, in `~/.se-agents/retros/`: what went well, every mistake, bug and failure, a scored judgement of each agent, and a `## Usage` table of measured token use per agent (from `python ~/.se-agents/usage.py`). Retros describe the team's behavior, never the product: no product or client names, code, paths, URLs, emails or secrets.

## How retros are used

Run `/judge-retros` in Claude Code in this repository. It reads every retro in `~/.se-agents/retros/` (or a folder you name), clusters recurring problems and cost hot spots, flags any drop in quality after a change to the agents, checks whether a later commit already fixed each problem, and writes `REPORT.md` with ranked, concrete changes to the agents. A person decides what to change, through "Changing the team" in `AGENTS.md`.
