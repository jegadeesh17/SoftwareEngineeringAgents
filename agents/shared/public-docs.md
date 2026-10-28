### Public documents and code

Everything that gets committed is read by people who never saw this build. That covers the documents (`README.md`, `CHANGELOG.md`, `docs/README.md`, `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/DEPLOYMENT.md`, `PRODUCT.md`, `DESIGN.md`) and also source code, tests, comments, docstrings, test names and commit messages. Write them for a human engineer reading the repository:
- Never name team roles or sub-agents, task IDs (such as `M1-TASK-03`), milestone or attempt numbers, review verdicts, viva or seam-lock terms, or workflow phases ("Phase 2.2"). Cite behavior, acceptance criteria (`AC-14`) and ADRs (`ADR-0007`) instead: a test comment says what it proves, not which task asked for it.
- Never link to or cite the private documents (`PROJECT_MENTAL_MODEL.md`, `TASKS.json`, `QA_RESULTS.json`, review logs, and so on). The private documents may cite tasks; committed files may not.
- Attribute decisions to "we" or to the project owner, never to an agent.
