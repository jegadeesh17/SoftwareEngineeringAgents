"""
Orchestrator Engine
Coordinates the multi-agent team across the project lifecycle with strict HITL and Evaluator-Optimizer verification.
"""

import json
from pathlib import Path
from typing import Optional, Callable
from engine.config import ConfigManager
from engine.state import ProjectState, Stage, TaskItem
from engine.tools.workspace import WorkspaceTool
from engine.tools.terminal import TerminalTool

class OrchestratorEngine:
    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace = WorkspaceTool(workspace_dir)
        self.terminal = TerminalTool(workspace_dir)
        self.config_mgr = ConfigManager()
        self.state = ProjectState()

    def start_brainstorming(self, user_initial_idea: str) -> str:
        """Step 1: Elicit clarification, explain trade-offs, and crystallize the idea."""
        self.state.user_idea = user_initial_idea
        self.state.stage = Stage.BRAINSTORMING

        summary = (
            f"Thank you for sharing your vision! As your Lead Engineering Orchestrator and Technical Mentor, "
            f"I have analyzed your initial idea: '{user_initial_idea}'.\n\n"
            f"[Mentor Note] In professional software engineering, we avoid jumping straight to code.\n"
            f"Instead, we first eliminate ambiguities to prevent expensive rewrites later.\n\n"
            f"Let us collaborate on 4 key architectural decisions:\n"
            f"1. Target Users: Who will use this app directly, and what is their skill level?\n"
            f"2. Core Workflows: What are the 2-3 most important actions a user takes?\n"
            f"3. Data & Storage Trade-offs:\n"
            f"   - Option A: Local files/SQLite (Lightweight, zero-setup, runs locally)\n"
            f"   - Option B: Client-server / Cloud DB (Scalable, multi-device, requires server infrastructure)\n"
            f"   Which matches your expectations?\n"
            f"4. Delivery Interface: Do you prefer a Web UI, Desktop CLI, or REST API?"
        )
        return summary

    def synthesize_scope(self, answers_text: str) -> str:
        """Step 2: Synthesize answers into a locked scope proposal with learning takeaways."""
        self.state.clarifications.append({"answers": answers_text})
        self.state.stage = Stage.APPROVAL_GATE

        proposal = (
            f"===========================================================\n"
            f"PROPOSED APPLICATION SCOPE (COLLABORATIVE SPECIFICATION)\n"
            f"===========================================================\n"
            f"Vision: {self.state.user_idea}\n"
            f"Clarifications & Decisions:\n{answers_text}\n\n"
            f"[Engineering Takeaway: Why We Establish Contracts First]\n"
            f"In enterprise software firms (MNCs), before allocating developer resources,\n"
            f"the Engagement Lead and Client agree on a formal scope boundary.\n"
            f"This prevents 'Scope Creep'—the #1 reason software projects fail or miss deadlines.\n\n"
            f"Deliverables Planned:\n"
            f"  - Formal PRD with User Stories & Acceptance Tests (docs/PRD.md)\n"
            f"  - Technical Architecture & Data Schemas (docs/ARCHITECTURE.md)\n"
            f"  - Decomposed Task Backlog (docs/TASKS.json)\n"
            f"  - Full Code Implementation & Automated Test Suite (verified via test runner)\n"
            f"===========================================================\n"
            f"APPROVAL REQUIRED: Do you approve this scope and authorize the engineering team to build? (yes/no)"
        )
        self.state.approved_scope = proposal
        return proposal

    def approve_scope(self, approved: bool) -> bool:
        """Human-in-the-loop approval gate."""
        if approved:
            self.state.stage = Stage.PRD_GENERATION
            return True
        else:
            self.state.stage = Stage.BRAINSTORMING
            return False

    def generate_prd(self) -> str:
        """Step 3: Product Analyst generates PRD.md."""
        content = (
            f"# Product Requirements Document (PRD)\n\n"
            f"## 1. Executive Summary\n"
            f"{self.state.user_idea}\n\n"
            f"## 2. Requirements & Scope\n"
            f"{self.state.approved_scope}\n\n"
            f"## 3. Acceptance Criteria (Given / When / Then)\n"
            f"- **Scenario 1**: Given valid user inputs, when executed, then the system must produce expected results.\n"
            f"- **Scenario 2**: Given unexpected or erroneous inputs, when processed, then the system must handle them gracefully without crashing.\n"
            f"- **Scenario 3**: System must pass all automated test suites with exit code 0.\n\n"
            f"## 4. Engineering Takeaway\n"
            f"Acceptance criteria act as the unambiguous contract between product design and QA testing.\n"
            f"They remove guesswork and allow QA to write automated assertions before coding even begins (Test-Driven Development).\n"
        )
        self.workspace.write_file("docs/PRD.md", content)
        self.state.prd_content = content
        self.state.stage = Stage.ARCHITECTURE_DESIGN
        return content

    def generate_architecture(self) -> str:
        """Step 4: Software Architect generates ARCHITECTURE.md."""
        content = (
            f"# Technical Architecture Document\n\n"
            f"## 1. System Overview\n"
            f"Architecture generated based on approved PRD.\n\n"
            f"## 2. Technology Stack & Trade-off Rationale\n"
            f"- Runtime: Python 3.13+\n"
            f"- Test Framework: pytest / unittest\n"
            f"- Design Pattern: Modular service architecture with clear interface boundaries.\n\n"
            f"## 3. Directory Layout\n"
            f"- `src/`: Core implementation modules\n"
            f"- `tests/`: Automated unit & integration tests\n"
            f"- `docs/`: PRD, Architecture, and Task Backlog\n\n"
            f"## 4. Engineering Takeaway\n"
            f"Separation of concerns (SoC): By keeping data models, business logic, and tests in distinct modules,\n"
            f"developers can modify one component without causing unexpected side-effects in another.\n"
        )
        self.workspace.write_file("docs/ARCHITECTURE.md", content)
        self.state.architecture_content = content
        self.state.stage = Stage.TASK_PLANNING
        return content

    def plan_tasks(self, default_tasks: Optional[list] = None) -> list:
        """Step 5: Task Planner decomposes architecture into tasks."""
        tasks = default_tasks or [
            {
                "id": "TASK-01",
                "title": "Project Scaffolding & Core Models",
                "description": "Create src/ structure and foundational data models.",
                "files_to_create": ["src/__init__.py", "src/models.py"],
                "files_to_modify": [],
                "acceptance_criteria": "Models instantiate and validate attributes cleanly.",
                "status": "pending"
            },
            {
                "id": "TASK-02",
                "title": "Core Business Logic",
                "description": "Implement main services in src/core.py.",
                "files_to_create": ["src/core.py"],
                "files_to_modify": [],
                "acceptance_criteria": "Service executes workflows without unhandled exceptions.",
                "status": "pending"
            },
            {
                "id": "TASK-03",
                "title": "Automated Test Suite & Verification",
                "description": "Write comprehensive tests in tests/test_core.py.",
                "files_to_create": ["tests/__init__.py", "tests/test_core.py"],
                "files_to_modify": [],
                "acceptance_criteria": "All unit tests pass with exit code 0.",
                "status": "pending"
            }
        ]

        task_items = [TaskItem(**t) for t in tasks]
        self.state.tasks = task_items
        self.workspace.write_file("docs/TASKS.json", json.dumps({"tasks": tasks}, indent=2))
        self.state.stage = Stage.IMPLEMENTATION_TESTING
        return tasks

    def execute_evaluator_optimizer_loop(self, task: TaskItem, test_command: str) -> dict:
        """Step 6: Evaluator-Optimizer loop between Developer and QA Tester."""
        task.attempts += 1
        test_result = self.terminal.run_command(test_command)

        if test_result.passed:
            task.status = "completed"
            task.test_logs = test_result.stdout
            if task.id not in self.state.completed_tasks:
                self.state.completed_tasks.append(task.id)
            return {"success": True, "result": test_result, "attempts": task.attempts}
        else:
            task.status = "failed"
            task.test_logs = f"STDOUT:\n{test_result.stdout}\nSTDERR:\n{test_result.stderr}"
            return {"success": False, "result": test_result, "attempts": task.attempts}
