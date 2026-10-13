import re
from pathlib import Path

import pytest

from engine import retros

ROOT = Path(__file__).parent.parent
SAMPLE = (ROOT / "tests" / "fixtures" / "retro_sample.md").read_text(encoding="utf-8")
FILLED = {
    "sea_commit": "4e3fbc4", "runtime": "claude-code", "orchestrator_model": "opus", "started": "2026-10-13",
    "finished": "", "project_type": "Streamlit dashboard", "existing_code": "no", "ui": "yes",
    "sensitive_data": "no", "deploy": "no", "change_type": "new", "milestones_planned": "3",
    "milestones_accepted": "0", "outcome": "in-progress",
}


def _set(text, key, value):
    return re.sub(rf"^{key}:.*$", f"{key}: {value}", text, count=1, flags=re.MULTILINE)


def test_sample_is_valid_and_clean():
    assert retros.validate(SAMPLE) == []
    assert retros.privacy_findings(SAMPLE, []) == []


def test_template_with_placeholders_filled_is_valid():
    template = (ROOT / "templates" / "retro.md").read_text(encoding="utf-8")
    filled = re.sub(r"^(\w+): <[^>]*>$", lambda m: f"{m.group(1)}: {FILLED[m.group(1)]}", template,
                    flags=re.MULTILINE)

    assert retros.validate(filled) == []
    assert set(retros.parse(filled)[0]) == retros.KEYS


def test_parse_returns_frontmatter_and_body():
    front, body = retros.parse(SAMPLE)

    assert front["project_type"] == "Streamlit dashboard"
    assert body.lstrip().startswith("## Summary")


def test_missing_frontmatter_is_an_error():
    assert retros.validate("## Summary\n") == ["missing frontmatter: the file must start with a --- block"]


@pytest.mark.parametrize("text, expected", [
    (SAMPLE.replace("deploy: no\n", ""), "missing key: deploy"),
    (SAMPLE.replace("deploy: no\n", "deploy: no\nmood: great\n"), "unknown key: mood"),
    (_set(SAMPLE, "runtime", "vscode"), "runtime"),
    (_set(SAMPLE, "started", "13-10-2026"), "started"),
    (_set(SAMPLE, "finished", ""), "finished is required"),
    (_set(SAMPLE, "milestones_accepted", "4"), "milestones_accepted"),
    (_set(SAMPLE, "milestones_planned", "three"), "milestones_planned"),
    (SAMPLE.replace("deploy: no\n", "deploy: no\ndeploy: yes\n"), "duplicate key: deploy"),
    (SAMPLE.replace("## Scores", "## Ratings"), "sections must be"),
    (SAMPLE.replace("| bug | medium |", "| oops | medium |"), "kind"),
    (SAMPLE.replace("| went-well | - |", "| went-well | high |"), "went-well"),
    (SAMPLE.replace("| bug | medium |", "| bug | - |"), "severity"),
    (SAMPLE.replace("| 3 | 4 | 3 | 5 |", "| 6 | 4 | 3 | 5 |"), "score"),
    (SAMPLE.replace("| 3 | 4 | 3 | 5 |", "| 3 | 4 | 3 |"), "columns"),
    (_set(SAMPLE, "project_type", "<generic type, for example Streamlit dashboard>"), "placeholder"),
    (_set(SAMPLE, "finished", "2026-10-01"), "before started"),
])
def test_validate_reports_each_problem(text, expected):
    errors = retros.validate(text)

    assert any(expected in error for error in errors), errors


def test_in_progress_retro_may_leave_finished_empty():
    text = _set(_set(SAMPLE, "outcome", "in-progress"), "finished", "")

    assert retros.validate(text) == []


def test_crlf_and_bom_are_accepted():
    assert retros.validate("\ufeff" + SAMPLE.replace("\n", "\r\n")) == []


@pytest.mark.parametrize("line, kind", [
    ("Saved to C:\\Users\\jo\\app", "absolute path"),
    ("Saved to /home/jo/app", "absolute path"),
    ("Saved to /Users/jo/app", "absolute path"),
    ("Mail jo@example.com", "email"),
    ("Token ghp_abcdefghijklmnop", "secret"),
    ("See https://example.com/x", "url"),
    ("Key 3f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c", "secret-like string"),
    ("Deployed to acme-shop.vercel.app", "hostname"),
    ("Database at 192.168.1.20:5432", "ip address"),
    ("Specs on \\\\fileserver\\acme\\specs", "absolute path"),
    ("Venv in ~/projects/acme-shop/.venv", "absolute path"),
    ("Served from /var/www/acme/app.py", "absolute path"),
    ("Saved to /users/jo/app", "absolute path"),
    ("Set in %USERPROFILE%", "absolute path"),
    ("Key AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY", "secret"),
    ("Token xoxb-123456789012-abcdefghijkl", "secret"),
    ("Token glpat-abcdefghij1234567890", "secret"),
    ("Connect postgres://u:p@localhost/db", "url"),
])
def test_privacy_findings_flag_each_pattern_with_its_line(line, kind):
    findings = retros.privacy_findings(f"first line\n{line}\n", [])

    assert any(f.startswith(f"line 2: {kind}") for f in findings), findings


def test_this_repositorys_url_is_allowed():
    assert retros.privacy_findings("https://github.com/jegadeesh17/SoftwareEngineeringAgents/issues", []) == []


def test_real_usernames_are_flagged_as_whole_words():
    findings = retros.privacy_findings("jsmith fixed it\njsmithson did not\n", ["jsmith"])

    assert findings == ["line 1: username: jsmith"]


def test_generic_usernames_are_not_flagged():
    assert retros.privacy_findings("The user accepted M1. The runner was slow.", ["user", "runner", "ab"]) == []


def test_container_logins_are_not_flagged():
    text = "runtime: claude-code\nnode_modules was missing; the vscode terminal and ubuntu image were fine"

    assert retros.privacy_findings(text, ["code", "claude", "node", "vscode", "ubuntu", "codespace"]) == []


def test_file_names_and_the_team_folder_are_not_flagged():
    text = "Edited orchestrator.md, test_retros.py and package.json; could not write ~/.se-agents/retros; see github.com"

    assert retros.privacy_findings(text, []) == []


def test_snake_case_names_with_digits_are_not_secrets():
    text = "test_oauth2_callback_rejects_expired_state_after_retry_3 failed twice"

    assert retros.privacy_findings(text, []) == []


def test_mixed_case_key_with_underscore_is_still_a_secret():
    findings = retros.privacy_findings("token Ab3dEf9hIjKlMn0pQrStUv_WxYz1234AbCd", [])

    assert any("secret-like string" in f for f in findings), findings


def test_lookalike_of_this_repositorys_url_is_flagged():
    findings = retros.privacy_findings("https://github.com/jegadeesh17/SoftwareEngineeringAgentsEvil/x", [])

    assert any(": url: " in f for f in findings), findings


def test_escaped_pipes_inside_cells_are_one_cell():
    text = SAMPLE.replace("An empty list showed", "Clicking a \\| b showed an empty list; it showed")

    assert retros.validate(text) == []


def test_table_without_separator_row_is_an_error():
    text = SAMPLE.replace("|---|---|---|---|---|---|---|---|---|\n", "")

    assert any("separator" in error for error in retros.validate(text))


def test_long_identifiers_without_digits_are_not_secrets():
    text = ("test_orchestrator_prompt_stays_within_its_line_budget failed; frontend-developer-and-ui-reviewer-conflict; "
            "see docs/superpowers/specs/2026-10-13-team-retro-design")

    assert retros.privacy_findings(text, []) == []


def test_cli_checks_files_and_folders(tmp_path, capsys):
    good = tmp_path / "good.md"
    good.write_text(SAMPLE, encoding="utf-8")
    bad = tmp_path / "sub" / "bad.md"
    bad.parent.mkdir()
    bad.write_text(SAMPLE.replace("project_type: Streamlit dashboard", "project_type: see C:\\work"), encoding="utf-8")

    assert retros.main([str(good)]) == 0
    assert retros.main([str(tmp_path / "sub")]) == 1
    assert "absolute path" in capsys.readouterr().out
    assert retros.main([]) == 2


def test_contributed_retros_are_valid_and_clean():
    # CI gate for community pull requests: a malformed or unsafe retro fails here
    for path in sorted((ROOT / "retros" / "community").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        assert retros.validate(text) == [], path.name
        assert retros.privacy_findings(text, []) == [], path.name


def test_judge_command_reads_retros_and_never_edits_agents():
    text = (ROOT / ".claude" / "commands" / "judge-retros.md").read_text(encoding="utf-8")

    assert text.startswith("---\n")
    for expected in ("model: opus", "effort: high", "python -m engine.retros", "retros/REPORT.md",
                     "git log", "Preserve", "Never edit"):
        assert expected in text, expected
