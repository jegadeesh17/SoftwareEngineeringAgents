# SoftwareEngineeringAgents

Autonomous software engineering team orchestration for non-technical vibe coders.

## Core Philosophy: Capability × AI Leverage
The Orchestrator acts as both a **Delivery Manager** and a **Technical Mentor**. Communication is bidirectional:
- Rather than an opaque vending machine that spits out code, the Orchestrator ensures the user learns how engineering teams design, make trade-offs, and verify systems.
- Every major phase includes an **Engineering Takeaway** demystifying the underlying concepts.

## System Topology & Roles
This repository operates as a managed software engineering department:
- **Lead Orchestrator / Mentor**: Brainstorms with user, surfaces trade-offs, enforces Human-In-The-Loop (HITL) approval, and leads the specialized team.
- **Product Analyst** (`skills/product-analyst`): Translates conversations into `docs/SPEC.md` and living `docs/PROJECT_MENTAL_MODEL.md`.
- **Software Architect** (`skills/software-architect`): Designs technical contracts in `docs/ARCHITECTURE.md` and records ADRs in `docs/DECISIONS.md`.
- **Task Planner** (`skills/task-planner`): Decomposes architecture into 3 Milestones (M1 MVP, M2 Core, M3 Polish) in `docs/TASKS.json`.
- **Software Developer** (`skills/software-developer`): Follows the 5-step build discipline to implement task-by-task.
- **QA Tester** (`skills/qa-tester`): Writes automated tests and executes them in the terminal for deterministic verification.
- **Adversarial Reviewer** (`skills/adversarial-reviewer`): Stress-tests implementation for silent failures, schema drift, and security.
- **DevOps & Git Disciplinarian** (`skills/devops-git`): Enforces atomic Conventional Commits at milestone boundaries to preserve full history.

## Observability & Telemetry Standard
- Every agent invocation, input prompt, tool execution, and token metric is recorded to `.orchestrator/traces/session_<id>.jsonl`.
- Provides full auditability without external SaaS dependency or network bloat.

## Operational Standards
1. **Bidirectional Learning**: Clarify requirements while explaining *why* technical trade-offs matter.
2. **Human Gate**: Never start coding without explicit user confirmation on the synthesized scope.
3. **Deterministic Verification**: No task is completed without running real tests via terminal tools.
4. **Git Discipline**: Every milestone is committed with clear Conventional Commit messages.
5. **Living Docs Sync**: Automatically checks off completed steps in `docs/PROJECT_STATUS.md`.
