import subprocess
import sys
from pathlib import Path

import pytest

from engine.config import ConfigManager
from engine.observability import ObservabilityLayer
from engine.orchestrator import OrchestratorEngine
from engine.tools.terminal import TerminalTool


def test_engine_keeps_all_output_inside_workspace(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    eng = OrchestratorEngine(workspace_dir=workspace)
    eng.pre_flight_scoping("Todo app")

    assert list(elsewhere.iterdir()) == []
    assert Path(eng.telemetry.trace_file).parent == workspace / ".orchestrator" / "traces"
    assert (workspace / "docs" / "PROJECT_STATUS.md").exists()


def test_run_command_supports_shell_syntax_on_posix(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    terminal = TerminalTool(tmp_path)

    res = terminal.run_command('python -c "print(1)" && python -c "print(2)"')

    assert res.passed
    assert res.stdout.split() == ["1", "2"]


def test_run_command_reports_timeout(tmp_path):
    terminal = TerminalTool(tmp_path)

    res = terminal.run_command(
        'python -c "print(\'started\', flush=True); import time; time.sleep(3)"', timeout=1
    )

    assert not res.passed
    assert res.exit_code == 124
    assert res.stderr == "Execution timed out after 1 seconds"
    assert isinstance(res.stdout, str)


def _git_repo(path):
    def git(*args):
        return subprocess.run(["git", *args], cwd=path, capture_output=True, text=True)

    git("init", "-q")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.com")
    git("config", "commit.gpgsign", "false")
    (path / "a.py").write_text("a = 1\n")
    (path / "b.py").write_text("b = 2\n")
    return git


def test_commit_milestone_commits_message_verbatim_and_only_given_files(tmp_path):
    git = _git_repo(tmp_path)
    eng = OrchestratorEngine(workspace_dir=tmp_path)

    ok = eng.commit_milestone("feat", "m1", 'add "quoted" parser', ["a.py"])

    assert ok
    assert git("log", "-1", "--format=%s").stdout.strip() == 'feat(m1): add "quoted" parser'
    assert git("show", "--name-only", "--format=").stdout.split() == ["a.py"]


def test_commit_milestone_without_files_does_not_stage_everything(tmp_path):
    git = _git_repo(tmp_path)
    eng = OrchestratorEngine(workspace_dir=tmp_path)

    ok = eng.commit_milestone("feat", "m1", "add parser", [])

    assert not ok
    assert git("rev-parse", "--verify", "HEAD").returncode != 0


MODEL_ENV_VARS = [
    "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY",
    "ANTHROPIC_MODEL", "GEMINI_MODEL", "OPENAI_MODEL",
]


def test_config_respects_model_env_var_without_api_key(tmp_path, monkeypatch):
    for var in MODEL_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "my-custom-model")

    cfg = ConfigManager(tmp_path / "config.json")

    assert cfg.get_active_provider() == "openai"
    assert cfg.get_active_model() == "my-custom-model"


def test_config_warns_on_corrupt_file_and_falls_back(tmp_path, monkeypatch):
    for var in MODEL_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    config_file = tmp_path / "config.json"
    config_file.write_text("{not json", encoding="utf-8")

    with pytest.warns(UserWarning, match="config.json"):
        cfg = ConfigManager(config_file)

    assert cfg.get_active_provider() == "gemini"


def test_sessions_started_together_get_separate_trace_files(tmp_path):
    first = ObservabilityLayer(tmp_path)
    second = ObservabilityLayer(tmp_path)

    assert first.trace_file != second.trace_file
