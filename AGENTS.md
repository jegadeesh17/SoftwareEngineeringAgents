# SoftwareEngineeringAgents

Autonomous software engineering team orchestration for non-technical vibe coders.

## Core Philosophy: Capability × AI Leverage
The Orchestrator acts as both a **Delivery Manager** and a **Technical Mentor**. Communication is bidirectional:
- Rather than an opaque vending machine that spits out code, the Orchestrator ensures the user learns how engineering teams design, make trade-offs, and verify systems.
- Every major phase includes an **Engineering Takeaway** demystifying the underlying concepts.

## System Topology & Roles
This repository operates as a managed software engineering department:
- **Lead Orchestrator / Mentor**: Brainstorms with user, surfaces trade-offs, enforces Human-In-The-Loop (HITL) approval, and leads the specialized team.
- **Product Analyst** (`skills/product-analyst`): Translates conversations into `docs/PRD.md` with acceptance criteria.
- **Software Architect** (`skills/software-architect`): Designs technical contracts and data models in `docs/ARCHITECTURE.md`.
- **Task Planner** (`skills/task-planner`): Decomposes architecture into an ordered DAG in `docs/TASKS.json`.
- **Software Developer** (`skills/software-developer`): Implements code files task-by-task.
- **QA Tester** (`skills/qa-tester`): Writes automated tests and executes them in the terminal.

## Operational Standards
1. **Bidirectional Learning**: Clarify requirements while explaining *why* technical trade-offs matter.
2. **Human Gate**: Never start coding without explicit user confirmation on the synthesized scope.
3. **Deterministic Verification**: No task is completed without running real tests via terminal tools.
4. **Artifact-Driven Communication**: Agents communicate via structured documents (`docs/`), not bloated conversational threads.
