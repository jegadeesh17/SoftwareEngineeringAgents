import importlib.util
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from engine import build_agents

ROOT = Path(__file__).parent.parent


def _text(path):
    return path.read_text(encoding="utf-8")


def _copy_repo(repo):
    for name in ("agents", ".claude", ".agents", "templates"):
        shutil.copytree(ROOT / name, repo / name)
    return repo


@pytest.fixture
def installer(monkeypatch):
    # The installer must never shell out. Record instead of running, so a regression
    # (like the old `pip install -e`) fails the test without touching the real environment.
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: calls.append(a))
    spec = importlib.util.spec_from_file_location("install_global", ROOT / "scripts" / "install_global.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module
    assert calls == [], f"installer ran a subprocess: {calls}"


def test_installer_installs_team_for_both_tools(tmp_path, installer):
    assert installer.main([], home=tmp_path) == 0

    # Compare content, not bytes: a fresh autocrlf clone has CRLF files, the installer writes LF
    assert _text(tmp_path / ".claude" / "agents" / "qa-tester.md") == _text(ROOT / ".claude" / "agents" / "qa-tester.md")
    assert _text(tmp_path / ".claude" / "commands" / "orchestrate.md") == \
        _text(ROOT / "templates" / "claude" / "orchestrate.md")
    assert _text(tmp_path / ".gemini" / "config" / "agents" / "orchestrator" / "agent.md") == \
        _text(ROOT / ".agents" / "agents" / "orchestrator" / "agent.md")
    assert len(list((tmp_path / ".claude" / "agents").glob("*.md"))) == 7
    assert len(list((tmp_path / ".gemini" / "config" / "agents").glob("*/agent.md"))) == 8


def test_installer_keeps_customized_slash_command(tmp_path, installer, capsys):
    existing = tmp_path / ".claude" / "commands" / "orchestrate.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("my customized command\n", encoding="utf-8")

    assert installer.main([], home=tmp_path) == 1

    assert existing.read_text(encoding="utf-8") == "my customized command\n"
    assert "1 file(s) skipped" in capsys.readouterr().out


def test_installer_overwrites_customized_slash_command_with_force(tmp_path, installer):
    existing = tmp_path / ".claude" / "commands" / "orchestrate.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("my customized command\n", encoding="utf-8")

    installer.main(["--force"], home=tmp_path)

    assert _text(existing) == _text(ROOT / "templates" / "claude" / "orchestrate.md")


def test_installer_skips_global_naming_rule_unless_requested(tmp_path, installer):
    rule = tmp_path / ".gemini" / "config" / "rules" / "nomenclature-standards.md"

    installer.main([], home=tmp_path)
    assert not rule.exists()

    installer.main(["--global-rules"], home=tmp_path)
    assert rule.exists()


def test_installer_rerun_skips_nothing(tmp_path, installer, capsys):
    installer.main([], home=tmp_path)
    capsys.readouterr()

    assert installer.main([], home=tmp_path) == 0

    assert "Skipped:" not in capsys.readouterr().out


def test_installer_flags_old_orchestrator_skill_without_deleting_it(tmp_path, installer, capsys):
    old_skill = tmp_path / ".gemini" / "config" / "skills" / "orchestrator" / "SKILL.md"
    old_skill.parent.mkdir(parents=True)
    old_skill.write_text("old skill\n", encoding="utf-8")

    installer.main([], home=tmp_path)

    assert old_skill.exists()
    assert "old 'orchestrator' skill" in capsys.readouterr().out


def test_installer_refuses_when_generated_files_are_stale(tmp_path, installer):
    repo = _copy_repo(tmp_path / "repo")
    with open(repo / "agents" / "qa-tester.md", "a", encoding="utf-8") as f:
        f.write("\nA new rule nobody regenerated.\n")
    home = tmp_path / "home"

    assert installer.main([], home=home, root=repo) == 1

    assert not home.exists()


def test_installer_writes_lf_and_ignores_line_ending_only_differences(tmp_path, installer, capsys):
    installed = tmp_path / ".claude" / "agents" / "qa-tester.md"
    installed.parent.mkdir(parents=True)
    lf = (ROOT / ".claude" / "agents" / "qa-tester.md").read_bytes().replace(b"\r\n", b"\n")
    installed.write_bytes(lf.replace(b"\n", b"\r\n"))

    assert installer.main([], home=tmp_path) == 0

    assert "Skipped:" not in capsys.readouterr().out
    assert b"\r\n" not in installed.read_bytes()


def test_installer_installs_lf_from_a_crlf_checkout(tmp_path, installer):
    repo = _copy_repo(tmp_path / "repo")
    for path in repo.rglob("*"):
        if path.is_file():
            path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    home = tmp_path / "home"

    assert installer.main([], home=home, root=repo) == 0

    for path in (
        home / ".claude" / "commands" / "orchestrate.md",
        home / ".gemini" / "config" / "agents" / "orchestrator" / "agent.md",
    ):
        assert b"\r\n" not in path.read_bytes()


def test_installer_updates_files_from_its_previous_install(tmp_path, installer, capsys):
    repo = _copy_repo(tmp_path / "repo")
    home = tmp_path / "home"
    assert installer.main([], home=home, root=repo) == 0
    with open(repo / "agents" / "qa-tester.md", "a", encoding="utf-8") as f:
        f.write("\nA new rule.\n")
    assert build_agents.main([], root=repo) == 0
    capsys.readouterr()

    assert installer.main([], home=home, root=repo) == 0

    assert "Skipped:" not in capsys.readouterr().out
    assert "A new rule." in _text(home / ".claude" / "agents" / "qa-tester.md")


def test_installer_replaces_the_old_installers_orchestrate_command(tmp_path, installer):
    command = tmp_path / ".claude" / "commands" / "orchestrate.md"
    command.parent.mkdir(parents=True)
    command.write_bytes((ROOT / "tests" / "fixtures" / "legacy_orchestrate.md").read_bytes())

    assert installer.main([], home=tmp_path) == 0

    assert _text(command) == _text(ROOT / "templates" / "claude" / "orchestrate.md")


def test_installer_reports_invalid_source_instead_of_suggesting_a_rebuild(tmp_path, installer, capsys):
    repo = _copy_repo(tmp_path / "repo")
    (repo / "agents" / "roles.toml").write_text("[roles.broken\n", encoding="utf-8")
    home = tmp_path / "home"

    assert installer.main([], home=home, root=repo) == 2

    out = capsys.readouterr()
    assert "roles.toml is not valid TOML" in out.err
    assert "out of date" not in out.out
    assert not home.exists()


def test_installer_notes_installed_roles_that_were_removed_from_the_team(tmp_path, installer, capsys):
    repo = _copy_repo(tmp_path / "repo")
    home = tmp_path / "home"
    assert installer.main([], home=home, root=repo) == 0
    manifest = repo / "agents" / "roles.toml"
    manifest.write_text(
        re.sub(r"\[roles\.devops-git\].*?(?=\n\[roles\.|\Z)", "", manifest.read_text(encoding="utf-8"), flags=re.S),
        encoding="utf-8",
    )
    (repo / "agents" / "devops-git.md").unlink()
    assert build_agents.main([], root=repo) == 0
    capsys.readouterr()

    assert installer.main([], home=home, root=repo) == 0

    out = capsys.readouterr().out
    assert "no longer part of the team" in out
    assert str(Path(".claude") / "agents" / "devops-git.md") in out
    assert (home / ".claude" / "agents" / "devops-git.md").exists()
