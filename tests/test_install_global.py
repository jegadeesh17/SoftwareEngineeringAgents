import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


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

    assert (tmp_path / ".claude" / "agents" / "qa-tester.md").read_bytes() == \
        (ROOT / ".claude" / "agents" / "qa-tester.md").read_bytes()
    assert (tmp_path / ".claude" / "commands" / "orchestrate.md").read_bytes() == \
        (ROOT / "templates" / "claude" / "orchestrate.md").read_bytes()
    assert (tmp_path / ".gemini" / "config" / "agents" / "orchestrator" / "agent.md").read_bytes() == \
        (ROOT / ".agents" / "agents" / "orchestrator" / "agent.md").read_bytes()
    assert len(list((tmp_path / ".claude" / "agents").glob("*.md"))) == 7
    assert len(list((tmp_path / ".gemini" / "config" / "agents").glob("*/agent.md"))) == 8


def test_installer_keeps_customized_slash_command(tmp_path, installer):
    existing = tmp_path / ".claude" / "commands" / "orchestrate.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("my customized command\n", encoding="utf-8")

    installer.main([], home=tmp_path)

    assert existing.read_text(encoding="utf-8") == "my customized command\n"


def test_installer_overwrites_customized_slash_command_with_force(tmp_path, installer):
    existing = tmp_path / ".claude" / "commands" / "orchestrate.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("my customized command\n", encoding="utf-8")

    installer.main(["--force"], home=tmp_path)

    assert existing.read_bytes() == (ROOT / "templates" / "claude" / "orchestrate.md").read_bytes()


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
    repo = tmp_path / "repo"
    for name in ("agents", ".claude", ".agents", "templates"):
        shutil.copytree(ROOT / name, repo / name)
    with open(repo / "agents" / "qa-tester.md", "a", encoding="utf-8") as f:
        f.write("\nA new rule nobody regenerated.\n")
    home = tmp_path / "home"

    assert installer.main([], home=home, root=repo) == 1

    assert not home.exists()
