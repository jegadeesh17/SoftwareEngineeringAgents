import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SAMPLE = (ROOT / "tests" / "fixtures" / "retro_sample.md").read_text(encoding="utf-8")


@pytest.fixture
def contribute():
    spec = importlib.util.spec_from_file_location("contribute_retro", ROOT / "scripts" / "contribute_retro.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def _git_repo(path):
    path.mkdir()
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test")
    _git(path, "config", "commit.gpgsign", "false")
    (path / "README.md").write_text("x\n", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(path, "commit", "-q", "-m", "init")
    return path


def _clone_with_local_commit(tmp_path):
    """An upstream repo, and a user's clone of it with one private commit on top."""
    upstream = _git_repo(tmp_path / "upstream")
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", str(upstream), str(clone)], check=True)
    _git(clone, "config", "user.email", "test@example.com")
    _git(clone, "config", "user.name", "Test")
    _git(clone, "config", "commit.gpgsign", "false")
    (clone / "agents.md").write_text("my private customization\n", encoding="utf-8")
    _git(clone, "add", "agents.md")
    _git(clone, "commit", "-q", "-m", "private customization")
    return upstream, clone


def _retro(tmp_path, text=SAMPLE):
    path = tmp_path / "retro.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_target_name_is_anonymous_and_slugged(contribute):
    front = {"started": "2026-10-13", "project_type": "Streamlit / ML dashboard!"}

    assert contribute.target_name(front, token="abc123") == "2026-10-13-streamlit-ml-dashboard-abc123.md"
    assert contribute.slug("!!!") == "project"


def test_dry_run_blocks_a_retro_with_a_privacy_finding(tmp_path, contribute, capsys):
    path = _retro(tmp_path, SAMPLE.replace("An empty list", "C:\\work\\shop: an empty list"))

    assert contribute.main([str(path), "--dry-run"], home=tmp_path) == 1
    assert "absolute path" in capsys.readouterr().out


def test_dry_run_blocks_an_invalid_retro(tmp_path, contribute, capsys):
    path = _retro(tmp_path, SAMPLE.replace("deploy: no\n", ""))

    assert contribute.main([str(path), "--dry-run"], home=tmp_path) == 1
    assert "missing key: deploy" in capsys.readouterr().out


def test_dry_run_prints_the_anonymous_target(tmp_path, contribute, capsys):
    assert contribute.main([str(_retro(tmp_path)), "--dry-run"], home=tmp_path) == 0
    assert re.search(r"retros/community/2026-10-13-streamlit-dashboard-[0-9a-f]{6}\.md", capsys.readouterr().out)


def test_chooses_from_the_central_folder_newest_first(tmp_path, contribute, capsys):
    folder = tmp_path / ".se-agents" / "retros"
    folder.mkdir(parents=True)
    oldest = folder / "old.md"
    oldest.write_text(SAMPLE.replace("deploy: no\n", ""), encoding="utf-8")
    os.utime(oldest, (1_000_000, 1_000_000))  # explicit: two quick writes can share an mtime on Windows
    (folder / "new.md").write_text(SAMPLE, encoding="utf-8")

    assert contribute.main(["--dry-run"], home=tmp_path, ask=lambda prompt: "1") == 0
    assert contribute.main(["--dry-run"], home=tmp_path, ask=lambda prompt: "9") == 1


def test_commits_on_a_new_branch_and_returns_to_the_original(tmp_path, contribute):
    upstream, repo = _clone_with_local_commit(tmp_path)
    asked = []

    code = contribute.main([str(_retro(tmp_path))], home=tmp_path, root=repo, upstream=str(upstream),
                           ask=lambda prompt: asked.append(prompt) or "n")

    assert code == 0
    assert _git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    branch = _git(repo, "branch", "--list", "retro/*").strip()
    assert re.fullmatch(r"retro/2026-10-13-streamlit-dashboard-[0-9a-f]{6}", branch)
    added = _git(repo, "show", "--name-only", "--format=", branch)
    assert re.fullmatch(r"retros/community/2026-10-13-streamlit-dashboard-[0-9a-f]{6}\.md", added)
    assert _git(repo, "log", "-1", "--format=%s", branch).startswith("docs(retros): add ")
    assert asked == ["Open a pull request now? [y/N] "]


def test_branch_starts_from_upstream_so_local_commits_stay_private(tmp_path, contribute):
    upstream, repo = _clone_with_local_commit(tmp_path)

    assert contribute.main([str(_retro(tmp_path))], home=tmp_path, root=repo, upstream=str(upstream),
                           ask=lambda prompt: "n") == 0

    branch = _git(repo, "branch", "--list", "retro/*").strip()
    subjects = _git(repo, "log", "--format=%s", branch).splitlines()
    assert subjects[1:] == ["init"]
    assert subjects[0].startswith("docs(retros): add ")


def test_refuses_when_upstream_cannot_be_fetched(tmp_path, contribute, capsys):
    _, repo = _clone_with_local_commit(tmp_path)

    assert contribute.main([str(_retro(tmp_path))], home=tmp_path, root=repo, upstream=str(tmp_path / "missing"),
                           ask=lambda prompt: "n") == 1
    assert "could not fetch" in capsys.readouterr().out
    assert _git(repo, "branch", "--list", "retro/*") == ""


def test_refuses_an_unfinished_retro(tmp_path, contribute, capsys):
    text = SAMPLE.replace("outcome: completed", "outcome: in-progress")

    assert contribute.main([str(_retro(tmp_path, text)), "--dry-run"], home=tmp_path) == 1
    assert "in-progress" in capsys.readouterr().out


def test_later_hint_works_in_powershell(tmp_path, contribute, capsys):
    upstream, repo = _clone_with_local_commit(tmp_path)

    contribute.main([str(_retro(tmp_path))], home=tmp_path, root=repo, upstream=str(upstream), ask=lambda prompt: "n")

    out = capsys.readouterr().out
    assert "&&" not in out
    assert re.search(r"^\s+git switch retro/\S+$", out, re.MULTILINE)
    assert re.search(r"^\s+gh pr create --fill$", out, re.MULTILINE)


@pytest.mark.parametrize("command, message", [
    (["gh-command-that-does-not-exist"], "not installed"),
    ([sys.executable, "-c", "raise SystemExit(1)"], "could not open"),
])
def test_exits_1_when_the_pull_request_is_not_opened(tmp_path, contribute, capsys, monkeypatch, command, message):
    upstream, repo = _clone_with_local_commit(tmp_path)
    monkeypatch.setattr(contribute, "GH_COMMAND", command)

    code = contribute.main([str(_retro(tmp_path))], home=tmp_path, root=repo, upstream=str(upstream),
                           ask=lambda prompt: "y")

    assert code == 1
    assert message in capsys.readouterr().out
    assert _git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"


def test_explains_a_missing_git(tmp_path, contribute, capsys, monkeypatch):
    monkeypatch.setattr(contribute, "GIT", "git-command-that-does-not-exist")

    assert contribute.main([str(_retro(tmp_path))], home=tmp_path, root=tmp_path, ask=lambda prompt: "n") == 1
    assert "git is not installed" in capsys.readouterr().out


def test_explains_a_folder_that_is_not_a_clone(tmp_path, contribute, capsys):
    folder = tmp_path / "download"
    folder.mkdir()

    assert contribute.main([str(_retro(tmp_path))], home=tmp_path, root=folder, ask=lambda prompt: "n") == 1
    assert "not a git clone" in capsys.readouterr().out


def test_expands_a_home_relative_path(tmp_path, contribute, monkeypatch):
    _retro(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    assert contribute.main(["~/retro.md", "--dry-run"], home=tmp_path) == 0


def test_refuses_a_dirty_clone(tmp_path, contribute, capsys):
    repo = _git_repo(tmp_path / "repo")
    (repo / "notes.txt").write_text("wip\n", encoding="utf-8")

    assert contribute.main([str(_retro(tmp_path))], home=tmp_path, root=repo, ask=lambda prompt: "n") == 1
    assert "uncommitted changes" in capsys.readouterr().out
    assert _git(repo, "branch", "--list", "retro/*") == ""
