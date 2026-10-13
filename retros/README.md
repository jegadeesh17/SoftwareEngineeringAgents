# Team retros

Every project the team builds leaves a retro on the builder's machine, in `~/.se-agents/retros/`: what went well, and every mistake, bug and failure, plus a scored judgement of each agent. Retros describe the team's behavior, never the product: no product or client names, code, paths, URLs, emails or secrets.

## Contribute yours

From your clone of this repository:

    python scripts/contribute_retro.py

It lists your retros, checks the one you pick for format and privacy problems, copies it into `community/` under an anonymous name on a new branch, and asks before opening a pull request with the GitHub CLI. Add `--dry-run` to check a retro without changing anything. CI runs the same checks on every pull request.

## How retros are used

Maintainers run `/judge-retros` in Claude Code. It clusters recurring problems across all retros in `community/`, checks whether a later commit already fixed them, and writes `REPORT.md` with ranked, concrete changes to the agents. A person decides what to change.
