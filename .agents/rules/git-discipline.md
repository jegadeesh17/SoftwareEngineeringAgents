---
description: Git version control standards and atomic milestone commit rules
globs: ["*"]
always_on: true
---

# Git Discipline & Historical Integrity Rules

All agents operating in `SoftwareEngineeringAgents` must maintain strict version control discipline. Historical information must never be overwritten, truncated, or lost.

## 1. Conventional Commits Standard
Every commit authored by the team must follow the Conventional Commits specification:
- `feat(scope)`: New user features, services, or models
- `docs(scope)`: Specifications (`SPEC.md`, `ARCHITECTURE.md`, `PROJECT_STATUS.md`)
- `test(scope)`: Test suites, verification harnesses, and assertions
- `refactor(scope)`: Code restructurings without behavior changes
- `chore(scope)`: Configuration, dependencies, and environment files

## 2. Milestone Atomic Commits
Never batch a giant pile of unrelated changes into a single generic commit. The **DevOps & Git Agent** commits at each discrete milestone:
1. `docs(scoping)`: Initial mental model and status tracker
2. `docs(spec)`: Finalized `docs/SPEC.md`
3. `docs(arch)`: System architecture and ADRs (`docs/ARCHITECTURE.md`, `docs/DECISIONS.md`)
4. `feat(m1)`: Milestone 1 MVP implementation and passing tests
5. `feat(m2)`: Milestone 2 Core flows implementation and passing tests
6. `test(adversarial)`: Adversarial quality review and security clearance
7. `chore(release)`: Final Polish and retrospective handover

## 3. Preservation of History & Safety
- **Never Force Push (`git push -f`)**: History must remain immutable.
- **Never Overwrite Uncommitted Work**: Always verify `git status` before writing.
- **Respect .gitignore**: Secrets (`.env`), telemetry caches (`.orchestrator/`), and virtual environments (`.venv/`) must never be staged.
