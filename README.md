# SoftwareEngineeringAgents

> **An autonomous software engineering organization built for non-technical "vibe coders", powered by the PSB (Plan · Setup · Build) Automation Pipeline.**

You don't need to know how to write a PRD, design software architecture, decompose work, write code, or execute test suites. Furthermore, you no longer need to copy-paste prompts manually from prompt playbooks. 

You simply converse with the **Lead Engineering Orchestrator**, who automatically leads you through scoping, initializes your living mental model, and triggers a specialized team to build, test, adversarial-review, and verify your software.

---

## Evolution: From Manual Playbook to Autonomous Team

In [ProjectWorkflowAutomation](../ProjectWorkflowAutomation), the workflow required the user to manually copy and paste 10 chronological prompts into Claude Code to drive the project.

In **SoftwareEngineeringAgents**, that entire PSB pipeline is natively automated into an agentic team:
- **No manual prompt pasting**: The Orchestrator conducts the interactive interview (Phase 0 & 1).
- **Living Documentation**: Automatically initializes and updates `docs/PROJECT_MENTAL_MODEL.md` and `docs/SPEC.md`.
- **Automated Living Checklist**: Progress is continuously tracked and checked off in `docs/PROJECT_STATUS.md`.
- **Milestone-Driven Execution**: Work is decomposed into **Milestone 1 (MVP Vertical Slice)**, **Milestone 2 (Core Flows)**, and **Milestone 3 (Polish & Edge Cases)**.
- **The 5-Step Build Discipline**: Explore $\rightarrow$ Plan $\rightarrow$ Implement $\rightarrow$ Verify (exit code 0) $\rightarrow$ Adversarial Review.

---

## Organizational Structure

Modeled after project delivery teams in modern IT services and tech MNCs:

```mermaid
graph TD
    User([Client / Vibe Coder]) <-->|Phase 0 & 1: Scoping & UX Interview| EM[Lead Engineering Orchestrator]
    EM -->|Maintains| MM["docs/PROJECT_MENTAL_MODEL.md & docs/PROJECT_STATUS.md"]
    EM -->|Human Approval Gate| BA[Product Analyst]
    BA -->|docs/SPEC.md| Arch[Software Architect]
    Arch -->|docs/ARCHITECTURE.md & docs/DECISIONS.md| TL[Task Planner]
    TL -->|docs/TASKS.json (M1, M2, M3)| Dev[Software Developer]
    Dev -->|Code Changes| QA[QA Tester]
    QA -->|Terminal Test Proof (Exit Code 0)| Adv[Adversarial Reviewer]
    Adv -->|Stress-Test Audit: docs/ADVERSARIAL_REVIEW.md| EM
    EM -->|Deliver Verified Project & Retrospective| User
```

| Department Role | Primary Output | Operational Mandate |
| :--- | :--- | :--- |
| **Lead Orchestrator & Mentor** | `PROJECT_MENTAL_MODEL.md`, `PROJECT_STATUS.md` | Conducts scoping interview, surfaces trade-offs, enforces approval gate. |
| **Product Analyst** | `docs/SPEC.md` | Consolidates user stories and `Given / When / Then` acceptance criteria. |
| **Software Architect** | `docs/ARCHITECTURE.md`, `docs/DECISIONS.md` | Defines schemas, contracts, directory layouts, and ADRs. |
| **Task Planner** | `docs/TASKS.json` | Decomposes architecture into 3 sequential Milestones (M1, M2, M3). |
| **Software Developer** | Source code in `src/` | Follows 5-step build discipline; implements task-by-task. |
| **QA Tester** | `docs/QA_RESULTS.json`, test suites in `tests/` | Executes real terminal test runners (deterministic exit code verification). |
| **Adversarial Reviewer** | `docs/ADVERSARIAL_REVIEW.md` | Stress-tests implementation for silent failures, edge cases, and security. |

---

## Universal Compatibility

This repository is designed to run seamlessly across all major AI developer tools:

### 1. Antigravity CLI (`agy`) and Antigravity IDE
- **Discovery**: Automatically discovers `.agents/rules/` and `.agents/skills/`.
- **Usage**: Run `agy` in this repository or open the folder in Antigravity IDE. The Lead Orchestrator persona will automatically govern the conversation.

### 2. Claude Code CLI
- **Discovery**: Automatically reads `CLAUDE.md` at the repository root.
- **Usage**: Run `claude` in this repository. Claude Code adopts the Orchestrator protocol, maintains living docs, and executes the team pipeline.

### 3. Standalone Terminal Engine
- **Usage**: Run the interactive Python engine in any terminal:
  ```bash
  python -m engine.cli
  ```

---

## Sticky Model Detection & Selection

AI platforms remember your model preference across sessions. This engine mirrors that behavior:

1. **Sticky Session Cache**: Remembers your latest model choice in `.orchestrator/config.json`.
2. **Environment Variable Detection**: Respects `GEMINI_MODEL`, `ANTHROPIC_MODEL`, or `OPENAI_MODEL` if configured.
3. **Interactive Confirmation**: On startup, the engine displays:
   ```text
   [Orchestrator] Detected default model: gemini-2.5-pro (gemini)
                  (Retrieved from your previous session / environment settings)

   Press [Enter] to confirm and continue with this model,
   or type 'change' to customize models:
   ```
4. **Manual Override**: Typing `change` allows switching the global model or assigning specialized models to specific agents.

---

## Directory Structure

```text
SoftwareEngineeringAgents/
├── .agents/
│   ├── rules/
│   │   ├── orchestrator-governance.md   # Approval gates & client-engagement rules
│   │   ├── qa-verification.md           # Real terminal test execution requirements
│   │   └── psb-workflow-discipline.md   # Plan-Setup-Build standard & living docs
│   └── skills/
│       ├── product-analyst/SKILL.md     # Mental model -> docs/SPEC.md
│       ├── software-architect/SKILL.md  # docs/ARCHITECTURE.md & docs/DECISIONS.md
│       ├── task-planner/SKILL.md        # docs/TASKS.json (M1, M2, M3 Milestones)
│       ├── software-developer/SKILL.md  # 5-step build discipline implementation
│       ├── qa-tester/SKILL.md           # Terminal verification & checklist sync
│       └── adversarial-reviewer/SKILL.md # Quality & security stress testing
├── engine/                              # Standalone Python runner
│   ├── cli.py                           # Interactive CLI entrypoint
│   ├── config.py                        # Sticky model detection & cache
│   ├── state.py                         # Dataclasses & stage tracking
│   ├── orchestrator.py                  # Multi-agent coordinator & FSM
│   └── tools/
│       ├── workspace.py                 # File read/write tools
│       └── terminal.py                  # Real test runner
├── AGENTS.md                            # Universal agent guidelines
├── GEMINI.md                            # Antigravity workspace rules
├── CLAUDE.md                            # Claude Code CLI universal entrypoint
├── requirements.txt
└── README.md
```
