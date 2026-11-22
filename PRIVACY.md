# Privacy

SEA (Software Engineering Agents) is a set of prompts that runs inside your own Claude Code session. It has no server, collects nothing, and sends nothing to its author.

## What it reads

- **Your project folder:** the agents read your code and documents to plan, build, test and review your project.
- **Your git user name:** only if you agree to the "How this was built" credit, the orchestrator reads `git config user.name` to write that credit.

## What it stores, and where

Everything stays on your computer or in repositories you control:

- **In your project:** code, tests and documents in `docs/`, and, if you agreed, the credit line with your git user name in your project's `README.md`.
- **Team retro:** one Markdown log per build in `~/.sea/retros/`, recording what went well and what failed. It holds no code, paths, URLs, emails or secrets, is never committed, and is never sent anywhere. Delete it whenever you like.

## What it sends, and to whom

- **GitHub:** only if you choose a remote during setup, the orchestrator creates the repository (`gh repo create`, private by default) and pushes your branch (`git push`).
- **Package registries:** installing your project's dependencies, and Playwright for UI screenshots, downloads them from their public registries.

Your conversations with Claude are handled by Anthropic under its own terms; SEA adds nothing to that.

## Retention

SEA keeps no data anywhere outside your computer and your own repositories.

## Contact

Questions or concerns: open an issue at https://github.com/jegadeesh17/SoftwareEngineeringAgents/issues
