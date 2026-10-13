"""
Team retro format: parse, validate and privacy-scan a retro written by the orchestrator.

A retro is Markdown with flat `key: value` frontmatter and three sections, ## Summary,
## Scores and ## Log, in that order (see templates/retro.md).

Usage: python -m engine.retros FILE_OR_FOLDER...
Exits 1 if any retro has a format error or a privacy finding.
"""

import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

SECTIONS = ["Summary", "Scores", "Log"]
YES_NO = {"yes", "no"}
ENUMS: Dict[str, Set[str]] = {
    "retro_format": {"1"},
    "runtime": {"claude-code", "antigravity"},
    "existing_code": YES_NO,
    "ui": YES_NO,
    "sensitive_data": YES_NO,
    "deploy": YES_NO,
    "change_type": {"new", "Feature", "Fix", "Refactor", "Redesign", "Transformation"},
    "outcome": {"completed", "abandoned", "in-progress"},
}
FREE_TEXT = {"sea_commit", "orchestrator_model", "project_type"}
DATES = {"started", "finished"}
INTEGERS = {"milestones_planned", "milestones_accepted"}
KEYS = set(ENUMS) | FREE_TEXT | DATES | INTEGERS

LOG_KINDS = {"went-well", "mistake", "bug", "failure", "user-correction", "hand-off-gap", "environment", "conflict"}
SEVERITIES = {"low", "medium", "high"}
SCORES = {"1", "2", "3", "4", "5", "n/a"}
LOG_COLUMNS = 9
SCORE_COLUMNS = 6

REPO_URL = "https://github.com/jegadeesh17/SoftwareEngineeringAgents"
# The repository itself, not a lookalike such as .../SoftwareEngineeringAgentsFork
ALLOWED_URL = re.compile(re.escape(REPO_URL) + r"(?:\.git)?(?:[/#?]|$)")
SEPARATOR_ROW = re.compile(r"\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?")
UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")
# Login names that are ordinary words in a retro ("the user") or common container and CI accounts
# ("node", "vscode"); scanning for them flags every retro and blocks honest contributions
GENERIC_USERNAMES = {
    "user", "users", "admin", "administrator", "root", "runner", "home", "owner", "dev", "test", "guest",
    "node", "vscode", "codespace", "codespaces", "ubuntu", "debian", "ec2-user", "docker", "app", "coder",
    "gitpod", "jovyan", "vagrant", "claude", "code",
}
URL = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://[^\s)>|]+")
PATTERNS = [
    ("absolute path", re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")),
    ("absolute path", re.compile(r"(?i)/(?:users|home|var|opt|srv|root|mnt|tmp|workspaces?)/[^/\s]+")),
    ("absolute path", re.compile(r"\\\\[^\s\\]+\\")),
    # ~/.se-agents is the team's own folder; retros may name it when a write there fails
    ("absolute path", re.compile(r"~[\\/](?!\.se-agents\b)")),
    ("absolute path", re.compile(r"(?i)%USERPROFILE%|\$HOME\b")),
    ("email", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("secret", re.compile(
        r"\b(?:sk-|sk_live_|rk_live_|ghp_|gho_|github_pat_|glpat-|xox[abposr]-|npm_|AIza|AKIA)[A-Za-z0-9_-]{8,}")),
    ("url", URL),
]
# Checked with URLs removed, so a URL is reported once, as a URL
HOSTNAME = re.compile(
    r"(?i)\b(?:[a-z0-9-]+\.)+(?:com|net|org|io|dev|app|ai|co|me|info|biz|xyz|cloud|site|tech|online|store"
    r"|in|uk|us|de|fr|eu|ca|au|local|internal|lan|corp)\b")
ALLOWED_HOSTS = {"github.com"}
IP_ADDRESS = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# No '-' here: hyphenated names such as docs paths with dates would otherwise read as keys
TOKEN_RUN = re.compile(r"[A-Za-z0-9+/=_]{32,}")


def normalize(text: str) -> str:
    """Strip a UTF-8 BOM and convert CRLF to LF, so a file saved on Windows parses the same."""
    return text.lstrip("﻿").replace("\r\n", "\n")


def _split(text: str) -> Optional[Tuple[List[str], str]]:
    lines = normalize(text).split("\n")
    if lines[0].strip() != "---":
        return None
    for end in range(1, len(lines)):
        if lines[end].strip() == "---":
            return lines[1:end], "\n".join(lines[end + 1:])
    return None


def parse(text: str) -> Tuple[Dict[str, str], str]:
    """The frontmatter as a dict, and the body after it. Without frontmatter: ({}, the whole text)."""
    split = _split(text)
    if split is None:
        return {}, normalize(text)
    front_lines, body = split
    front: Dict[str, str] = {}
    for line in front_lines:
        key, sep, value = line.partition(":")
        if sep and key.strip() and key.strip() not in front:
            front[key.strip()] = value.strip()
    return front, body


def _is_date(value: str) -> bool:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _section(body: str, name: str) -> str:
    match = re.search(rf"^## {name}[ \t]*$(.*?)(?=^## |\Z)", body, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


def _cells(row: str) -> List[str]:
    """A table row's cells. An escaped pipe (\\|) stays inside its cell."""
    cells = UNESCAPED_PIPE.split(row)
    if cells and not cells[0].strip():
        cells = cells[1:]
    if cells and not cells[-1].strip():
        cells = cells[:-1]
    return [cell.strip() for cell in cells]


def _table_rows(section: str, name: str) -> Tuple[List[List[str]], List[str]]:
    """Data rows of the Markdown table in a section, and an error if its header or separator row is missing."""
    rows = [line.strip() for line in section.split("\n") if line.strip().startswith("|")]
    if not rows:
        return [], []
    if len(rows) < 2 or not SEPARATOR_ROW.fullmatch(rows[1]):
        return [_cells(row) for row in rows[1:]], [f"{name} table: the second row must be the |---| separator row"]
    return [_cells(row) for row in rows[2:]], []


def _validate_frontmatter(front_lines: List[str]) -> List[str]:
    errors: List[str] = []
    front: Dict[str, str] = {}
    for line in front_lines:
        if not line.strip():
            continue
        key, sep, value = line.partition(":")
        key = key.strip()
        if not sep or not key:
            errors.append(f"frontmatter line is not 'key: value': {line.strip()}")
        elif key in front:
            errors.append(f"duplicate key: {key}")
        else:
            front[key] = value.strip()

    errors += [f"missing key: {key}" for key in sorted(KEYS - set(front))]
    errors += [f"unknown key: {key}" for key in sorted(set(front) - KEYS)]
    for key, allowed in ENUMS.items():
        if key in front and front[key] not in allowed:
            errors.append(f"{key}: '{front[key]}' is not one of {', '.join(sorted(allowed))}")
    for key in sorted(FREE_TEXT):
        if key in front and not front[key]:
            errors.append(f"{key} is empty")
    for key in sorted(front):
        if front[key].startswith("<"):
            errors.append(f"{key} still holds the template placeholder: {front[key]}")
    if "started" in front and not _is_date(front["started"]):
        errors.append(f"started: '{front['started']}' is not a YYYY-MM-DD date")
    if front.get("finished") and not _is_date(front["finished"]):
        errors.append(f"finished: '{front['finished']}' is not a YYYY-MM-DD date")
    if _is_date(front.get("started", "")) and _is_date(front.get("finished", "")) \
            and front["finished"] < front["started"]:
        errors.append("finished is before started")
    if front.get("outcome") in {"completed", "abandoned"} and not front.get("finished"):
        errors.append("finished is required when outcome is completed or abandoned")

    numbers: Dict[str, int] = {}
    for key in sorted(INTEGERS):
        if key in front:
            if front[key].isdigit():
                numbers[key] = int(front[key])
            else:
                errors.append(f"{key}: '{front[key]}' is not a whole number")
    if len(numbers) == 2 and numbers["milestones_accepted"] > numbers["milestones_planned"]:
        errors.append("milestones_accepted is larger than milestones_planned")
    return errors


def _validate_tables(body: str) -> List[str]:
    score_rows, errors = _table_rows(_section(body, "Scores"), "Scores")
    log_rows, log_errors = _table_rows(_section(body, "Log"), "Log")
    errors += log_errors
    for number, cells in enumerate(score_rows, start=1):
        if len(cells) != SCORE_COLUMNS:
            errors.append(f"scores row {number}: expected {SCORE_COLUMNS} columns, found {len(cells)}")
            continue
        for value in cells[1:5]:
            if value not in SCORES:
                errors.append(f"scores row {number}: score '{value}' is not 1-5 or n/a")
    for number, cells in enumerate(log_rows, start=1):
        if len(cells) != LOG_COLUMNS:
            errors.append(f"log row {number}: expected {LOG_COLUMNS} columns, found {len(cells)}")
            continue
        kind, severity = cells[3], cells[4]
        if kind not in LOG_KINDS:
            errors.append(f"log row {number}: kind '{kind}' is not one of {', '.join(sorted(LOG_KINDS))}")
        elif kind == "went-well" and severity != "-":
            errors.append(f"log row {number}: went-well rows use severity '-'")
        elif kind != "went-well" and severity not in SEVERITIES:
            errors.append(f"log row {number}: severity '{severity}' is not low, medium or high")
    return errors


def validate(text: str) -> List[str]:
    """Every format problem in a retro, as readable messages. An empty list means the retro is valid."""
    split = _split(text)
    if split is None:
        return ["missing frontmatter: the file must start with a --- block"]
    front_lines, body = split
    errors = _validate_frontmatter(front_lines)
    headings = re.findall(r"^## (.+?)[ \t]*$", body, re.MULTILINE)
    if headings != SECTIONS:
        expected = ", ".join(f"## {name}" for name in SECTIONS)
        errors.append(f"sections must be {expected} in that order; found {', '.join(headings) or 'none'}")
    else:
        errors += _validate_tables(body)
    return errors


def privacy_findings(text: str, usernames: List[str]) -> List[str]:
    """Lines that could identify the user or their project, as 'line N: kind: match'."""
    names = sorted({n.strip() for n in usernames
                    if len(n.strip()) >= 3 and n.strip().lower() not in GENERIC_USERNAMES})
    name_patterns = [(n, re.compile(rf"(?<![A-Za-z0-9]){re.escape(n)}(?![A-Za-z0-9])", re.IGNORECASE))
                     for n in names]
    findings: List[str] = []
    for number, line in enumerate(normalize(text).split("\n"), start=1):
        for kind, pattern in PATTERNS:
            for match in pattern.finditer(line):
                if kind == "url" and ALLOWED_URL.match(match.group(0)):
                    continue
                findings.append(f"line {number}: {kind}: {match.group(0)}")
        # URLs are reported (or allowed) above; scanning their parts again would double-report them
        without_urls = URL.sub(" ", line)
        for match in HOSTNAME.finditer(without_urls):
            if match.group(0).lower() not in ALLOWED_HOSTS:
                findings.append(f"line {number}: hostname: {match.group(0)}")
        for match in IP_ADDRESS.finditer(without_urls):
            findings.append(f"line {number}: ip address: {match.group(0)}")
        for match in TOKEN_RUN.finditer(without_urls):
            run = match.group(0)
            # Lowercase snake_case with digits is an identifier (test_oauth2_...), not a key
            identifier = "_" in run and not re.search(r"[A-Z]", run)
            if re.search(r"\d", run) and re.search(r"[A-Za-z]", run) and not identifier:
                findings.append(f"line {number}: secret-like string: {run}")
        for name, pattern in name_patterns:
            if pattern.search(line):
                findings.append(f"line {number}: username: {name}")
    return findings


def _retro_files(paths: List[str]) -> List[Path]:
    files: List[Path] = []
    for name in paths:
        path = Path(name).expanduser()
        files.extend(sorted(path.glob("*.md")) if path.is_dir() else [path])
    return files


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    paths = sys.argv[1:] if argv is None else argv
    if not paths:
        print("usage: python -m engine.retros FILE_OR_FOLDER...")
        return 2
    files = _retro_files(paths)
    if not files:
        print("No retros found.")
        return 0
    status = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"{path}: cannot read ({exc})")
            status = 1
            continue
        problems = validate(text) + privacy_findings(text, [])
        if problems:
            status = 1
            print(f"{path}:")
            for problem in problems:
                print(f"  - {problem}")
        else:
            print(f"{path}: OK")
    return status


if __name__ == "__main__":
    sys.exit(main())
