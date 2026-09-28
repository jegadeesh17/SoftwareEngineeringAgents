---
description: The PSB (Plan · Setup · Build) standard and living documentation rules
globs: ["*"]
always_on: true
---

# PSB (Plan · Setup · Build) Automation Standard

This repository follows the **PSB Workflow Standard** derived from `ProjectWorkflowAutomation`. The multi-agent team enforces this workflow autonomously so the user does not have to manually drive prompt playbooks.

## 1. Living Documentation Suite
The agents must maintain four living documents in `docs/`:
1. `docs/PROJECT_MENTAL_MODEL.md`: Captures the evolving understanding, scoping decisions, UX flows, and constraints.
2. `docs/SPEC.md`: The authoritative consolidated product specification and acceptance criteria.
3. `docs/ARCHITECTURE.md` & `docs/DECISIONS.md`: System design, schemas, API contracts, and architectural decision records (ADRs).
4. `docs/PROJECT_STATUS.md`: The single source of truth for project progress. Agents must automatically check off items as steps complete.

## 2. The 4 Project Phases

### Phase 0: Pre-Flight Scoping
- **Goal Classification**: Prototype (speed & minimal vertical slice) vs. Production Service (resilience, typed schemas, and comprehensive tests).
- **3-Milestone Decomposition**:
  - **Milestone 1 (MVP)**: Thinnest vertical slice proving end-to-end functionality.
  - **Milestone 2**: Core feature completion and secondary flows.
  - **Milestone 3**: Edge case handling, performance tuning, and polish.
- **Timebox Management**: ~20% Plan/Setup, ~60% Build, ~20% Polish.

### Phase 1: PLAN (Spec Formulation)
- Orchestrator interviews the user with 3-4 targeted questions at a time.
- Capture UX journeys, error states, and explicit non-goals in `docs/PROJECT_MENTAL_MODEL.md`.
- Consolidate into `docs/SPEC.md`.

### Phase 2: SETUP (Foundational Scaffolding)
- Scaffolding, `.env.example`, living doc initialization, and directory layout.

### Phase 3: BUILD (The 5-Step Verification Discipline)
Every task or milestone runs through:
1. **Explore**: Inspect relevant contracts and existing code.
2. **Plan**: Declare files to create/modify and acceptance tests.
3. **Implement**: Developer Agent writes modular code.
4. **Verify**: QA Tester Agent runs deterministic terminal commands (exit code 0 required).
5. **Adversarial Review**: Adversarial Reviewer Agent stress-tests for edge cases, silent failures, and schema drift.
6. **Sync Status**: Automatically update `docs/PROJECT_STATUS.md`.

### Phase 4: FINAL POLISH
- Audit repo diff, clean-state fresh install check, and user handover retrospective.
