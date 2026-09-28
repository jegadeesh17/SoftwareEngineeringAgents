"""
Observability and Telemetry Layer for SoftwareEngineeringAgents
Tracks agent actions, prompts, responses, tool calls, token metrics, and execution latency.
Saves structured OpenInference-compatible JSONL trace logs to .orchestrator/traces/.
"""

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

class TraceSpan:
    def __init__(self, agent: str, stage: str, action: str, parent_id: Optional[str] = None):
        self.span_id = uuid.uuid4().hex[:12]
        self.parent_id = parent_id
        self.agent = agent
        self.stage = stage
        self.action = action
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.duration_ms: float = 0.0
        self.inputs: Dict[str, Any] = {}
        self.outputs: Dict[str, Any] = {}
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.total_tokens: int = 0
        self.status: str = "RUNNING"
        self.error_message: Optional[str] = None

    def record_input(self, data: Any):
        if isinstance(data, str):
            self.inputs["prompt"] = data
            # Industry heuristic: ~4 characters per token
            self.prompt_tokens = max(1, len(data) // 4)
        elif isinstance(data, dict):
            self.inputs.update(data)
            self.prompt_tokens = max(1, len(json.dumps(data)) // 4)

    def record_output(self, data: Any, status: str = "OK"):
        self.status = status
        if isinstance(data, str):
            self.outputs["response"] = data
            self.completion_tokens = max(1, len(data) // 4)
        elif isinstance(data, dict):
            self.outputs.update(data)
            self.completion_tokens = max(1, len(json.dumps(data)) // 4)
        self.total_tokens = self.prompt_tokens + self.completion_tokens

    def close(self, status: Optional[str] = None):
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        if status:
            self.status = status
        elif self.status == "RUNNING":
            self.status = "OK"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "timestamp": datetime.fromtimestamp(self.start_time).isoformat(),
            "agent": self.agent,
            "stage": self.stage,
            "action": self.action,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "tokens": {
                "prompt": self.prompt_tokens,
                "completion": self.completion_tokens,
                "total": self.total_tokens
            },
            "inputs": self.inputs,
            "outputs": self.outputs,
            "error": self.error_message
        }


class ObservabilityLayer:
    """Manages active session tracing, metrics calculation, and JSONL persistence."""

    def __init__(self, trace_dir: Optional[Path] = None):
        self.trace_dir = trace_dir or Path(".orchestrator") / "traces"
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.trace_file = self.trace_dir / f"session_{self.session_id}.jsonl"
        self.spans: List[TraceSpan] = []
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0

    def start_span(self, agent: str, stage: str, action: str, parent_id: Optional[str] = None) -> TraceSpan:
        span = TraceSpan(agent=agent, stage=stage, action=action, parent_id=parent_id)
        self.spans.append(span)
        return span

    def end_span(self, span: TraceSpan, output_data: Any = None, status: str = "OK"):
        if output_data is not None:
            span.record_output(output_data, status=status)
        span.close(status=status)
        
        self.total_prompt_tokens += span.prompt_tokens
        self.total_completion_tokens += span.completion_tokens
        self.total_tokens += span.total_tokens

        # Append to JSONL file immediately for real-time auditability
        with open(self.trace_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(span.to_dict()) + "\n")

    def get_summary(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "trace_file": str(self.trace_file),
            "total_spans": len(self.spans),
            "tokens": {
                "prompt": self.total_prompt_tokens,
                "completion": self.total_completion_tokens,
                "total": self.total_tokens
            },
            "active_spans": sum(1 for s in self.spans if s.status == "OK"),
            "failed_spans": sum(1 for s in self.spans if s.status == "ERROR"),
        }
