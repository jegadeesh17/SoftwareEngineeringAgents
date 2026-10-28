# Document templates

The orchestrator reads the template it needs from this file when it writes that document. The installer copies it to `~/.se-agents/doc-templates.md`.

**`docs/README.md` (docs index):** `# Project documentation` and a one-line purpose. Then a table with the columns Document (relative link), Purpose and Updated when, with one row per public living document (every living document when `Workflow docs: committed`). Never name a team role or agent.

**`docs/WALKTHROUGH.md` (plan walkthrough):** `# Plan walkthrough` and one sentence on what the project is. Then these sections, in plain English, with no code and no jargon a non-developer would not know:

- `## How it works for you`: one subsection per journey in `docs/SPEC.md`, as numbered steps in the form "You do X → the app does Y → you see Z", including what the user sees on an error or empty state. Under each journey, one line on what happens behind the scenes and what data is stored.
- `## How it is built`: a Mermaid `flowchart` of the components from `docs/ARCHITECTURE.md` (user, UI, services, storage, external APIs) and how data moves between them, then one sentence per component on its job.
- `## How the build will run`: one bullet per milestone from `docs/TASKS.json`: what it delivers, what the user can try at its end (the UAT checklist), and any key, account or decision the user must provide before it starts.
- `## Hard to change later`: the points from `## Expensive to change` in `docs/ARCHITECTURE.md`, one line each with why.
- `## Not included`: the non-goals from `docs/PROJECT_MENTAL_MODEL.md` and anything `docs/SPEC.md` defers to a later milestone.

**`docs/viva-log.md` (`principal_architect` only):** `# Viva log` and a one-line purpose. Then one `## <Milestone> round <n> (YYYY-MM-DD)` section per round with Question, Answer summary (at most 3 lines, the user's own reasoning), Grade and Follow-up. Never include grading keys.

**Root `README.md`**, in this order:

- `# <Project name>` and a one-sentence description.
- `## Features`: bullets from the journeys in `docs/SPEC.md`.
- `## Quick start`: prerequisites with versions from `## Setup requirements`, the install command, `cp .env.example .env` with "fill in the values", and the run command.
- `## Usage`: a real example command or steps, with the expected output.
- `## Running tests`: the full and one-file commands.
- `## Configuration`: a table of variable names and what each is for, from `.env.example`. Never values.
- `## Project structure`: from the directory layout in `docs/ARCHITECTURE.md`.
- `## Documentation`: links to `docs/README.md`, `docs/DECISIONS.md` and `CHANGELOG.md`.
- `## How this was built` (only when `README credit: yes`): "Designed and built by <owner, from `git config user.name`> with [SoftwareEngineeringAgents](<url>), a multi-agent workflow for Claude Code." In a `principal_architect` project, add: "I set the scope, architecture and key decisions (see [docs/DECISIONS.md](docs/DECISIONS.md)); the agents implemented and reviewed tasks under that plan." Leave out the link if there is no URL.
- `## License`: link the LICENSE file if one exists, otherwise "Not yet licensed. Choose one at https://choosealicense.com".

No badges, emojis or invented URLs.

**`CHANGELOG.md` header:** `# Changelog`, the standard Keep a Changelog 1.1.0 preamble ("All notable changes to this project will be documented in this file." and the lines saying it follows Keep a Changelog and Semantic Versioning), then `## [Unreleased]`. Never cut a version: releasing is the user's call.
