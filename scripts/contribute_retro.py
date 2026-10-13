"""
Contribute a team retro to SoftwareEngineeringAgents.

Checks a retro from ~/.se-agents/retros/ for format and privacy problems, copies it into
retros/community/ under an anonymous name on a new branch, commits it, and offers to open
a pull request with the GitHub CLI. Nothing is pushed without your yes.

Usage: python scripts/contribute_retro.py [PATH] [--dry-run]
"""

import argparse
import getpass
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from engine import retros  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RETROS_DIR = Path(".se-agents") / "retros"
COMMUNITY_DIR = Path("retros") / "community"
# The retro branch starts from here, never from the user's HEAD, so their own commits stay out of the PR
UPSTREAM_URL = "https://github.com/jegadeesh17/SoftwareEngineeringAgents.git"
UPSTREAM_BRANCH = "main"
GIT = "git"
GH_COMMAND = ["gh"]


def _input(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        return ""


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40].strip("-") or "project"


def target_name(frontmatter: Dict[str, str], token: Optional[str] = None) -> str:
    """Anonymous file name: start date, generic project type and a random suffix, never the folder name."""
    return f"{frontmatter['started']}-{slug(frontmatter['project_type'])}-{token or secrets.token_hex(3)}.md"


def _usernames(home: Path) -> List[str]:
    names = [home.name]
    try:
        names.append(getpass.getuser())
    except (OSError, KeyError):  # no login name set in this environment
        pass
    return names


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([GIT, *args], cwd=root, capture_output=True, text=True)


def _choose(home: Path, ask: Callable[[str], str]) -> Optional[Path]:
    folder = home / RETROS_DIR
    files = sorted(folder.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True) if folder.is_dir() else []
    if not files:
        print(f"No retros found in {folder}.")
        return None
    for number, path in enumerate(files, start=1):
        print(f"  {number}. {path.name}")
    answer = ask("Which retro do you want to contribute? Number: ").strip()
    if not answer.isdigit() or not 1 <= int(answer) <= len(files):
        print("No retro chosen.")
        return None
    return files[int(answer) - 1]


def _commit(root: Path, target: Path, text: str) -> bool:
    (root / target).parent.mkdir(parents=True, exist_ok=True)
    (root / target).write_text(retros.normalize(text), encoding="utf-8", newline="\n")
    _git(root, "add", target.as_posix())
    result = _git(root, "commit", "-m", f"docs(retros): add {target.stem}")
    if result.returncode == 0:
        return True
    print(f"Not contributed: git commit failed.\n{result.stderr.strip()}")
    _git(root, "rm", "-q", "--cached", target.as_posix())
    (root / target).unlink()
    return False


def _print_later(branch: str) -> None:
    # Two lines, not "a && b": Windows PowerShell 5.1 cannot parse &&
    print("Run these two commands from this folder:")
    print(f"    git switch {branch}")
    print("    gh pr create --fill")


def _offer_pull_request(root: Path, branch: str, ask: Callable[[str], str]) -> bool:
    """False only when the user asked for a pull request and it could not be opened."""
    if ask("Open a pull request now? [y/N] ").strip().lower() != "y":
        print("No pull request opened. When you are ready:")
        _print_later(branch)
        return True
    try:
        result = subprocess.run([*GH_COMMAND, "pr", "create", "--fill"], cwd=root)
    except FileNotFoundError:
        print("The GitHub CLI (gh) is not installed. Install it from https://cli.github.com, run 'gh auth login', then:")
        _print_later(branch)
        return False
    if result.returncode != 0:
        print("gh could not open the pull request. Fix the problem above, then:")
        _print_later(branch)
        return False
    return True


def main(argv: Optional[List[str]] = None, home: Optional[Path] = None, root: Optional[Path] = None,
         ask: Callable[[str], str] = _input, upstream: str = UPSTREAM_URL) -> int:
    parser = argparse.ArgumentParser(description="Contribute a team retro to SoftwareEngineeringAgents")
    parser.add_argument("path", nargs="?", help="the retro to contribute (default: choose from ~/.se-agents/retros/)")
    parser.add_argument("--dry-run", action="store_true", help="check the retro and print its target name; change nothing")
    args = parser.parse_args(argv)
    root = root or REPO_ROOT
    home = home or Path.home()

    source = Path(args.path).expanduser() if args.path else _choose(home, ask)
    if source is None:
        return 1
    try:
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"Cannot read {source}: {exc}")
        return 1

    problems = retros.validate(text) + retros.privacy_findings(text, _usernames(home))
    if problems:
        print(f"Not contributed: {source} needs changes first.")
        for problem in problems:
            print(f"  - {problem}")
        print("Edit the file, then run this script again.")
        return 1

    frontmatter = retros.parse(text)[0]
    if frontmatter["outcome"] == "in-progress":
        print(f"Not contributed: {source} is still in-progress. Finish the project (or mark it abandoned) first.")
        return 1
    target = COMMUNITY_DIR / target_name(frontmatter)
    if args.dry_run:
        print(f"OK: would add {target.as_posix()}")
        return 0

    if shutil.which(GIT) is None:
        print("Not contributed: git is not installed. Install it from https://git-scm.com, then run this script again.")
        return 1
    if _git(root, "rev-parse", "--is-inside-work-tree").returncode != 0:
        print(f"Not contributed: {root} is not a git clone. Clone the repository with")
        print(f"    git clone {UPSTREAM_URL}")
        print("and run this script from that clone.")
        return 1
    if _git(root, "status", "--porcelain").stdout.strip():
        print("Not contributed: this clone has uncommitted changes. Commit or stash them first.")
        return 1
    original = _git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if not original or original == "HEAD":
        print("Not contributed: check out a branch (for example main) first.")
        return 1
    if _git(root, "fetch", "-q", upstream, UPSTREAM_BRANCH).returncode != 0:
        print(f"Not contributed: could not fetch {UPSTREAM_BRANCH} from {upstream}. Check your connection and try again.")
        return 1
    branch = f"retro/{target.stem}"
    if _git(root, "switch", "-c", branch, "FETCH_HEAD").returncode != 0:
        print(f"Not contributed: could not create the branch {branch}.")
        return 1

    committed = opened = False
    try:
        committed = _commit(root, target, text)
        if committed:
            print(f"Committed {target.as_posix()} on the branch {branch}.")
            opened = _offer_pull_request(root, branch, ask)
    finally:
        _git(root, "switch", original)
    if not committed:
        _git(root, "branch", "-D", branch)
        return 1
    return 0 if opened else 1


if __name__ == "__main__":
    sys.exit(main())
