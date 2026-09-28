"""
Project State Definitions for SoftwareEngineeringAgents
Artifacts and progress tracking across the lifecycle.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

class Stage(str, Enum):
    PRE_FLIGHT_SCOPING = "pre_flight_scoping"
    SPEC_INTERVIEW = "spec_interview"
    APPROVAL_GATE = "approval_gate"
    SPEC_CONSOLIDATION = "spec_consolidation"
    ARCHITECTURE_DECISIONS = "architecture_decisions"
    MILESTONE_PLANNING = "milestone_planning"
    MILESTONE_EXECUTION = "milestone_execution"
    ADVERSARIAL_REVIEW = "adversarial_review"
    FINAL_POLISH = "final_polish"

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
class Milestone:
    id: str
    name: str
    tasks: List[TaskItem] = field(default_factory=list)
    status: str = "pending"

@dataclass
class TestResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    passed: bool

@dataclass
class ProjectState:
    stage: Stage = Stage.PRE_FLIGHT_SCOPING
    user_idea: str = ""
    goal_posture: str = "Prototype"  # Prototype or Production
    target_persona: str = ""
    clarifications: List[Dict[str, str]] = field(default_factory=list)
    approved_scope: str = ""
    mental_model_content: str = ""
    spec_content: str = ""
    architecture_content: str = ""
    decisions_content: str = ""
    milestones: List[Milestone] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    status_checklist: Dict[str, bool] = field(default_factory=dict)
    adversarial_verdict: str = "PENDING"
    verification_history: List[Dict[str, Any]] = field(default_factory=list)
