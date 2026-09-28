import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


@pytest.fixture
def installer(monkeypatch):
    spec = importlib.util.spec_from_file_location("install_global", ROOT / "scripts" / "install_global.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Record instead of raising: the installer catches exceptions around pip
    calls = []
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: calls.append(a))
    yield module
    assert calls == [], f"installer ran a subprocess despite --no-pip: {calls}"


def test_installer_keeps_customized_slash_command(tmp_path, installer):
    existing = tmp_path / ".claude" / "commands" / "orchestrate.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("my customized command\n", encoding="utf-8")

    installer.main(["--no-pip"], home=tmp_path)

    assert existing.read_text(encoding="utf-8") == "my customized command\n"


def test_installer_overwrites_customized_slash_command_with_force(tmp_path, installer):
    existing = tmp_path / ".claude" / "commands" / "orchestrate.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("my customized command\n", encoding="utf-8")

    installer.main(["--no-pip", "--force"], home=tmp_path)

    assert existing.read_bytes() == (ROOT / "templates" / "claude" / "orchestrate.md").read_bytes()


def test_installer_skips_global_naming_rule_unless_requested(tmp_path, installer):
    rule = tmp_path / ".gemini" / "config" / "rules" / "nomenclature-standards.md"

    installer.main(["--no-pip"], home=tmp_path)
    assert not rule.exists()

    installer.main(["--no-pip", "--global-rules"], home=tmp_path)
    assert rule.exists()
