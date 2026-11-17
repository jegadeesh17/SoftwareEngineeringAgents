# se-agents

An AI engineering team for Claude Code. Run `/se-agents:orchestrate` inside your project folder: the orchestrator interviews you, gets your approval on scope and architecture, then delegates to specialist sub-agents (codebase analyst, product analyst, architect, task planner, backend and frontend developers, platform engineer, QA tester, and adversarial, security and UI reviewers) through Plan, Setup and Build, and verifies every result itself.

Source, documentation and issues: https://github.com/jegadeesh17/SoftwareEngineeringAgents

## What it runs, reads and writes

The plugin ships Markdown prompts, two Markdown templates and one Python script. It has no MCP servers, no hooks and no network calls of its own.

- **In your project folder:** the agents read your code and write code, tests and documents in `docs/`. They run your project's own commands (tests, linters, builds) and `git` (init, branch, add, commit). Nothing outside your project is changed except the retro below.
- **GitHub:** only if you choose a remote during setup, the orchestrator runs `gh repo create` (private by default) or `git remote add`, and pushes your branch with `git push`. It never merges, force-pushes or deploys.
- **Team retro:** each build writes one Markdown log of what went well and what failed to `~/.se-agents/retros/` on your machine. It holds no code, paths, URLs or secrets and is never committed or sent anywhere.
- **Token usage:** `team/usage.py` (Python standard library only) reads Claude Code's local session transcripts in `~/.claude/projects/` for the current project and prints a token-usage table for the retro. It sends nothing.
- **Secrets:** you put secrets in `.env` yourself; the agents never print its contents, add it to `.gitignore` before the first commit and document variables in `.env.example`.

## License

MIT
