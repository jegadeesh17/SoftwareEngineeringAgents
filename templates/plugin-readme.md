# SEA: Software Engineering Agents

An AI engineering team for Claude Code, installed as the plugin `sea`. Run `/sea:orchestrate` inside your project folder: the orchestrator interviews you, gets your approval on scope and architecture, then delegates to specialist sub-agents (codebase analyst, product analyst, architect, task planner, backend and frontend developers, platform engineer, QA tester, and adversarial, security and UI reviewers) through Plan, Setup and Build, and verifies every result itself.

Source, documentation and issues: https://github.com/jegadeesh17/SoftwareEngineeringAgents

## What it runs, reads and writes

The plugin ships only Markdown: prompts and two templates. It has no scripts, no MCP servers and no hooks, and it sends no data to any service of its own.

- **In your project folder:** the agents read your code and write code, tests and documents in `docs/`. They run your project's own commands (dependency installs, tests, linters, builds) and `git` (init, branch, add, commit). Installing your project's dependencies downloads them from their package registries. Nothing outside your project is changed except the retro below.
- **UI screenshots:** for projects with a UI, the UI reviewer runs your app locally and screenshots it with `npx playwright screenshot` into `.ui-review/` in your project. If Playwright is not installed, `npx` downloads it from npm.
- **GitHub:** only if you choose a remote during setup, the orchestrator runs `gh repo create` (private by default) or `git remote add`, and pushes your branch with `git push`. It never merges, force-pushes or deploys.
- **Team retro:** each build writes one Markdown log of what went well and what failed to `~/.sea/retros/` on your machine. It holds no code, paths, URLs or secrets and is never committed or sent anywhere.
- **Secrets:** you put secrets in `.env` yourself; the agents never print its contents, add it to `.gitignore` before the first commit and document variables in `.env.example`.

## License

MIT
