"""
Token usage per agent for one project, measured from Claude Code's session transcripts.

Claude Code stores each session under ~/.claude/projects/<slug>/ as <session>.jsonl, and each
sub-agent run as <session>/subagents/agent-*.jsonl with its type in the sibling .meta.json.
This prints a Markdown table the orchestrator pastes into the team retro's ## Usage section.

Usage: python -m engine.usage PROJECT_DIR [--since YYYY-MM-DD] [--claude-home DIR]
The installer also copies this file to ~/.se-agents/usage.py, so it must stay standard-library only.
"""

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional

ORCHESTRATOR = "orchestrator"
MAIN_OTHER = "main (other)"
# Living documents whose repeated reads the retro reports; names only, so no project path leaks into it
LIVING_DOCS = {"README", "PROJECT_MENTAL_MODEL", "PROJECT_STATUS", "SPEC", "ARCHITECTURE", "DECISIONS", "TASKS",
               "WALKTHROUGH", "QA_RESULTS", "FEEDBACK", "CODEBASE_MAP", "DEPLOYMENT"}
TOP_DOCS = 5


@dataclass
class AgentUsage:
    runs: int = 0
    turns: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    peak_context: int = 0

    def add(self, other: "AgentUsage") -> None:
        self.runs += other.runs
        self.turns += other.turns
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.peak_context = max(self.peak_context, other.peak_context)


@dataclass
class Report:
    agents: Dict[str, AgentUsage] = field(default_factory=dict)
    doc_reads: Counter = field(default_factory=Counter)


def project_slug(project: Path) -> str:
    """Claude Code's folder name for a project: the absolute path with every non-alphanumeric character as '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(project.resolve()))


def transcript_dirs(project: Path, claude_home: Path) -> List[Path]:
    """Every transcript folder for the project; the drive letter's case can differ between sessions."""
    root = claude_home / "projects"
    if not root.is_dir():
        return []
    slug = project_slug(project).lower()
    return sorted(path for path in root.iterdir() if path.is_dir() and path.name.lower() == slug)


def _entries(path: Path, since: Optional[str]) -> Iterator[dict]:
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if since and str(entry.get("timestamp", ""))[:10] < since:
                    continue
                yield entry
    except OSError:
        return


def _doc_name(file_path: str) -> Optional[str]:
    name = re.split(r"[\\/]", file_path)[-1]
    stem, _, _ = name.rpartition(".")
    return name if stem in LIVING_DOCS or stem.endswith("_REVIEW") else None


def _scan(path: Path, since: Optional[str], report: Report) -> AgentUsage:
    """Usage in one transcript. Streamed replies repeat their usage, so each request is counted once."""
    requests: Dict[str, dict] = {}
    for entry in _entries(path, since):
        if entry.get("type") != "assistant":
            continue
        message = entry.get("message") or {}
        content = message.get("content")
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Read":
                doc = _doc_name(str((block.get("input") or {}).get("file_path", "")))
                if doc:
                    report.doc_reads[doc] += 1
        usage = message.get("usage")
        request_id = entry.get("requestId") or message.get("id")
        if not usage or not request_id or request_id in requests or message.get("model") == "<synthetic>":
            continue
        requests[request_id] = usage
    found = AgentUsage(runs=1 if requests else 0)
    for usage in requests.values():
        context = (usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0)
                   + usage.get("cache_creation_input_tokens", 0))
        found.turns += 1
        found.input_tokens += context
        found.output_tokens += usage.get("output_tokens", 0)
        found.peak_context = max(found.peak_context, context)
    return found


def _is_orchestrator_session(path: Path) -> bool:
    """A main session is the orchestrator's once /orchestrate ran in it; Claude Code tags only some turns."""
    return any(entry.get("attributionSkill") == "orchestrate" for entry in _entries(path, None))


def _agent_type(transcript: Path) -> str:
    try:
        meta = json.loads(transcript.with_suffix(".meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "unknown"
    return str(meta.get("agentType") or "unknown")


def collect(project: Path, claude_home: Path, since: Optional[str] = None) -> Report:
    report = Report()

    def add(label: str, usage: AgentUsage) -> None:
        report.agents.setdefault(label, AgentUsage()).add(usage)

    for folder in transcript_dirs(project, claude_home):
        for session in sorted(folder.glob("*.jsonl")):
            usage = _scan(session, since, report)
            if usage.runs:
                add(ORCHESTRATOR if _is_orchestrator_session(session) else MAIN_OTHER, usage)
            for transcript in sorted((folder / session.stem / "subagents").glob("agent-*.jsonl")):
                usage = _scan(transcript, since, report)
                if usage.runs:
                    add(_agent_type(transcript), usage)
    return report


def _row(name: str, usage: AgentUsage) -> str:
    turns_per_run = usage.turns / usage.runs if usage.runs else 0
    average = usage.input_tokens / usage.turns if usage.turns else 0
    return (f"| {name} | {usage.runs} | {usage.turns} | {turns_per_run:.0f} | {usage.input_tokens / 1e6:.1f} "
            f"| {usage.output_tokens / 1e3:.0f} | {average / 1e3:.0f} | {usage.peak_context / 1e3:.0f} |")


def render(report: Report) -> str:
    lines = ["| Agent | Runs | Turns | Turns/run | Input (M) | Output (k) | Avg context (k) | Peak context (k) |",
             "|---|---|---|---|---|---|---|---|"]
    total = AgentUsage()
    for name, usage in sorted(report.agents.items(), key=lambda item: -item[1].input_tokens):
        lines.append(_row(name, usage))
        total.add(usage)
    lines.append(_row("**Total**", total))
    if report.doc_reads:
        top = ", ".join(f"{name} ×{count}" for name, count in report.doc_reads.most_common(TOP_DOCS))
        lines += ["", f"Most re-read docs: {top}"]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="python -m engine.usage", description=__doc__.strip().splitlines()[0])
    parser.add_argument("project", type=Path, help="the project folder the team worked in")
    parser.add_argument("--since", help="count only sessions from this date on (YYYY-MM-DD)")
    parser.add_argument("--claude-home", type=Path, default=Path.home() / ".claude",
                        help="Claude Code's home folder (default: ~/.claude)")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if args.since and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.since):
        parser.error("--since must be YYYY-MM-DD")
    report = collect(args.project, args.claude_home.expanduser(), args.since)
    if not report.agents:
        print(f"Usage: no Claude Code transcripts found for {args.project}")
        return 0
    print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
