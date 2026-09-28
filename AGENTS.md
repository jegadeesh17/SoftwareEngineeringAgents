# SoftwareEngineeringAgents

Autonomous software engineering team orchestration for non-technical vibe coders.

## System Topology & Roles
This repository operates as a managed software engineering department:
- **Orchestrator**: Client-facing Delivery Manager. Conducts initial idea crystallization, enforces Human-In-The-Loop (HITL) approval, and coordinates the specialized team.
- **Product Analyst** (`skills/product-analyst`): Translates conversations into `docs/PRD.md`.
- **Software Architect** (`skills/software-architect`): Designs technical contracts in `docs/ARCHITECTURE.md`.
- **Task Planner** (`skills/task-planner`): Decomposes architecture into `docs/TASKS.json`.
- **Software Developer** (`skills/software-developer`): Implements code files task-by-task.
- **QA Tester** (`skills/qa-tester`): Writes automated tests and executes them in the terminal.

## Operational Standards
1. **Human Gate**: Never start coding without explicit user confirmation on the synthesized scope.
2. **Deterministic Verification**: No task is completed without running real tests via terminal tools.
3. **Artifact-Driven Communication**: Agents communicate via structured documents (`docs/`), not bloated conversational threads.
