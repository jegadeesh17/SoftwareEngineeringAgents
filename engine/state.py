"""
Project State Definitions for SoftwareEngineeringAgents
Artifacts and progress tracking across the lifecycle.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

class Stage(str, Enum):
    BRAINSTORMING = "brainstorming"
    APPROVAL_GATE = "approval_gate"
    PRD_GENERATION = "prd_generation"
    ARCHITECTURE_DESIGN = "architecture_design"
    TASK_PLANNING = "task_planning"
    IMPLEMENTATION_TESTING = "implementation_testing"
    DELIVERY = "delivery"

@dataclass
class TaskItem:
    id: str
    title: str
    description: str
    files_to_create: List[str]
    files_to_modify: List[str]
    acceptance_criteria: str
    status: str = "pending"  # pending, in_progress, completed, failed
    attempts: int = 0
    test_logs: str = ""

@dataclass
class TestResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    passed: bool

@dataclass
class ProjectState:
    stage: Stage = Stage.BRAINSTORMING
    user_idea: str = ""
    clarifications: List[Dict[str, str]] = field(default_factory=list)
    approved_scope: str = ""
    prd_content: str = ""
    architecture_content: str = ""
    tasks: List[TaskItem] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    verification_history: List[Dict[str, Any]] = field(default_factory=list)
