import pytest

from engine import build_agents

QA_TOML = """
[roles.qa-tester]
description = "Runs tests"
claude_tools = ["Read", "Bash"]
antigravity_tools = ["view_file", "run_command"]
"""

ORCH_TOML = """
[roles.orchestrator]
description = "Leads the team"
main_agent = true
antigravity_tools = ["view_file", "invoke_subagent"]
"""

QA_BANNER = (
    "<!-- GENERATED from agents/qa-tester.md — edit the source and run "
    "python -m engine.build_agents -->\n\n"
)


def make_source(root, toml_text, prompts):
    src = root / "agents"
    src.mkdir()
    (src / "roles.toml").write_text(toml_text, encoding="utf-8")
    for name, body in prompts.items():
        (src / f"{name}.md").write_text(body, encoding="utf-8")
    return root


def test_claude_agent_has_frontmatter_and_verbatim_body(tmp_path):
    make_source(tmp_path, QA_TOML, {"qa-tester": "# QA\n\nRun the tests.\n"})

    assert build_agents.main([], root=tmp_path) == 0

    text = (tmp_path / ".claude" / "agents" / "qa-tester.md").read_text(encoding="utf-8")
    assert text == (
        "---\n"
        "name: qa-tester\n"
        'description: "Runs tests Part of the /orchestrate engineering team: use only when the orchestrator delegates to it."\n'
        "tools: Read, Bash\n"
        "model: inherit\n"
        "---\n\n"
        + QA_BANNER
        + "# QA\n\nRun the tests.\n"
    )


def test_antigravity_agent_lists_tools_and_is_a_subagent(tmp_path):
    make_source(tmp_path, QA_TOML, {"qa-tester": "# QA\n\nRun the tests.\n"})

    assert build_agents.main([], root=tmp_path) == 0

    text = (tmp_path / ".agents" / "agents" / "qa-tester" / "agent.md").read_text(encoding="utf-8")
    assert text == (
        "---\n"
        "name: qa-tester\n"
        'description: "Runs tests Part of the /orchestrate engineering team: use only when the orchestrator delegates to it."\n'
        "tools:\n"
        "  - view_file\n"
        "  - run_command\n"
        "model: inherit\n"
        "mainAgent: false\n"
        "subagent: true\n"
        "---\n\n"
        + QA_BANNER
        + "# QA\n\nRun the tests.\n"
    )


def test_orchestrator_is_antigravity_main_agent_and_claude_slash_command(tmp_path):
    make_source(tmp_path, ORCH_TOML, {"orchestrator": "# Lead\n"})

    assert build_agents.main([], root=tmp_path) == 0

    agy = (tmp_path / ".agents" / "agents" / "orchestrator" / "agent.md").read_text(encoding="utf-8")
    assert "mainAgent: true\nsubagent: false\n" in agy
    assert "  - invoke_subagent\n" in agy
    command = (tmp_path / "templates" / "claude" / "orchestrate.md").read_text(encoding="utf-8")
    assert command == (
        "---\n"
        'description: "Leads the team"\n'
        "---\n\n"
        "<!-- GENERATED from agents/orchestrator.md — edit the source and run "
        "python -m engine.build_agents -->\n\n"
        "# Lead\n"
    )
    assert not (tmp_path / ".claude" / "agents").exists()


def test_description_with_quotes_and_colons_is_escaped(tmp_path):
    toml_text = QA_TOML.replace('"Runs tests"', "'Checks \"edge\" cases: all of them'")
    make_source(tmp_path, toml_text, {"qa-tester": "# QA\n"})

    assert build_agents.main([], root=tmp_path) == 0

    text = (tmp_path / ".claude" / "agents" / "qa-tester.md").read_text(encoding="utf-8")
    assert 'description: "Checks \\"edge\\" cases: all of them Part of the /orchestrate engineering team: use only when the orchestrator delegates to it."\n' in text


def test_crlf_unicode_source_produces_lf_utf8_output(tmp_path):
    make_source(tmp_path, QA_TOML, {})
    (tmp_path / "agents" / "qa-tester.md").write_bytes("# QA\r\n\r\nFail fast — always.\r\n".encode("utf-8"))

    assert build_agents.main([], root=tmp_path) == 0

    data = (tmp_path / ".claude" / "agents" / "qa-tester.md").read_bytes()
    assert b"\r\n" not in data
    assert data.endswith("# QA\n\nFail fast — always.\n".encode("utf-8"))


@pytest.mark.parametrize(
    "toml_text, prompts, message",
    [
        (QA_TOML, {}, "without a prompt file: qa-tester"),
        (QA_TOML, {"qa-tester": "x", "extra": "y"}, "without a roles.toml entry: extra"),
        (QA_TOML.replace("claude_tools", "claude_tool"), {"qa-tester": "x"}, "unknown keys: claude_tool"),
        (QA_TOML.replace('claude_tools = ["Read", "Bash"]\n', ""), {"qa-tester": "x"}, "sub-agents need 'claude_tools'"),
        (QA_TOML.replace('description = "Runs tests"\n', ""), {"qa-tester": "x"}, "'description' is required"),
        (
            ORCH_TOML + ORCH_TOML.replace("orchestrator", "second-lead"),
            {"orchestrator": "x", "second-lead": "y"},
            "only one main agent allowed, found: orchestrator, second-lead",
        ),
        ("[roles.qa-tester\n", {"qa-tester": "x"}, "roles.toml"),
    ],
)
def test_invalid_source_is_rejected_and_nothing_written(tmp_path, capsys, toml_text, prompts, message):
    make_source(tmp_path, toml_text, prompts)

    assert build_agents.main([], root=tmp_path) == 2

    assert message in capsys.readouterr().err
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / ".agents").exists()


def test_missing_manifest_is_reported(tmp_path, capsys):
    (tmp_path / "agents").mkdir()

    assert build_agents.main([], root=tmp_path) == 2

    assert "agents/roles.toml not found" in capsys.readouterr().err


def test_check_fails_until_built_then_passes(tmp_path, capsys):
    make_source(tmp_path, QA_TOML, {"qa-tester": "# QA\n"})

    assert build_agents.main(["--check"], root=tmp_path) == 1
    assert ".claude/agents/qa-tester.md" in capsys.readouterr().out

    assert build_agents.main([], root=tmp_path) == 0
    assert build_agents.main(["--check"], root=tmp_path) == 0


def test_check_detects_hand_edited_generated_file(tmp_path):
    make_source(tmp_path, QA_TOML, {"qa-tester": "# QA\n"})
    build_agents.main([], root=tmp_path)
    generated = tmp_path / ".agents" / "agents" / "qa-tester" / "agent.md"
    with open(generated, "a", encoding="utf-8") as f:
        f.write("tweak\n")

    assert build_agents.main(["--check"], root=tmp_path) == 1


def test_check_accepts_crlf_checkout(tmp_path):
    make_source(tmp_path, QA_TOML, {"qa-tester": "# QA\n"})
    build_agents.main([], root=tmp_path)
    generated = tmp_path / ".claude" / "agents" / "qa-tester.md"
    generated.write_bytes(generated.read_bytes().replace(b"\n", b"\r\n"))

    assert build_agents.main(["--check"], root=tmp_path) == 0


def test_build_removes_stale_generated_agents_but_keeps_hand_written(tmp_path):
    make_source(tmp_path, QA_TOML, {"qa-tester": "# QA\n"})
    build_agents.main([], root=tmp_path)
    stale_text = (
        "---\nname: old-role\n---\n\n"
        "<!-- GENERATED from agents/old-role.md — edit the source and run python -m engine.build_agents -->\n\nold\n"
    )
    stale_claude = tmp_path / ".claude" / "agents" / "old-role.md"
    stale_claude.write_text(stale_text, encoding="utf-8")
    stale_agy = tmp_path / ".agents" / "agents" / "old-role" / "agent.md"
    stale_agy.parent.mkdir(parents=True)
    stale_agy.write_text(stale_text, encoding="utf-8")
    hand_written = tmp_path / ".claude" / "agents" / "my-helper.md"
    hand_written.write_text("---\nname: my-helper\n---\n\nhand written\n", encoding="utf-8")

    assert build_agents.main(["--check"], root=tmp_path) == 1
    assert build_agents.main([], root=tmp_path) == 0

    assert not stale_claude.exists()
    assert not stale_agy.parent.exists()
    assert hand_written.exists()
    assert build_agents.main(["--check"], root=tmp_path) == 0


def test_committed_generated_files_match_source(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # the default root must be the repo, not the current directory

    assert build_agents.main(["--check"]) == 0


def test_team_roster_and_permissions():
    roles = {r.name: r for r in build_agents.load_roles(build_agents.REPO_ROOT / "agents")}

    assert set(roles) == {
        "orchestrator", "product-analyst", "software-architect", "task-planner",
        "software-developer", "qa-tester", "adversarial-reviewer", "devops-git",
    }
    assert [n for n, r in roles.items() if r.main_agent] == ["orchestrator"]
    # Without invoke_subagent the Antigravity orchestrator cannot delegate at all
    assert "invoke_subagent" in roles["orchestrator"].antigravity_tools
    # The reviewer must not be able to change the code it judges
    assert not {"Write", "Edit"} & set(roles["adversarial-reviewer"].claude_tools)
    assert not {"write_to_file", "replace_file_content"} & set(roles["adversarial-reviewer"].antigravity_tools)


@pytest.mark.parametrize(
    "toml_text, prompt_name, message",
    [
        (QA_TOML.replace('["Read", "Bash"]', '"Read, Bash"'), "qa-tester",
         "role 'qa-tester': 'claude_tools' must be a non-empty list of strings"),
        (QA_TOML.replace('["view_file", "run_command"]', "[]"), "qa-tester",
         "role 'qa-tester': 'antigravity_tools' must be a non-empty list of strings"),
        (QA_TOML.replace('"Runs tests"', "42"), "qa-tester",
         "role 'qa-tester': 'description' must be a non-empty string"),
        (ORCH_TOML.replace("main_agent = true", 'main_agent = "true"'), "orchestrator",
         "role 'orchestrator': 'main_agent' must be true or false"),
        (QA_TOML.replace("[roles.qa-tester]", '[roles."QA Tester"]'), "QA Tester",
         "invalid role name 'QA Tester'"),
    ],
)
def test_wrongly_typed_fields_are_rejected(tmp_path, capsys, toml_text, prompt_name, message):
    make_source(tmp_path, toml_text, {prompt_name: "x"})

    assert build_agents.main([], root=tmp_path) == 2

    assert message in capsys.readouterr().err
    assert not (tmp_path / ".claude").exists()
    assert not (tmp_path / ".agents").exists()


def test_build_keeps_hand_written_agents_copied_from_generated_ones(tmp_path):
    make_source(tmp_path, QA_TOML, {"qa-tester": "# QA\n"})
    build_agents.main([], root=tmp_path)
    claude_copy = tmp_path / ".claude" / "agents" / "my-strict-qa.md"
    claude_copy.write_text(
        (tmp_path / ".claude" / "agents" / "qa-tester.md").read_text(encoding="utf-8")
        .replace("name: qa-tester", "name: my-strict-qa"),
        encoding="utf-8",
    )
    agy_copy = tmp_path / ".agents" / "agents" / "my-strict-qa" / "agent.md"
    agy_copy.parent.mkdir()
    agy_copy.write_text(
        (tmp_path / ".agents" / "agents" / "qa-tester" / "agent.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    assert build_agents.main(["--check"], root=tmp_path) == 0
    assert build_agents.main([], root=tmp_path) == 0

    assert claude_copy.exists()
    assert agy_copy.exists()


def test_sub_agent_descriptions_are_scoped_to_the_orchestrator(tmp_path):
    make_source(tmp_path, QA_TOML + ORCH_TOML, {"qa-tester": "# QA\n", "orchestrator": "# Lead\n"})

    assert build_agents.main([], root=tmp_path) == 0

    scoped = 'description: "Runs tests Part of the /orchestrate engineering team: use only when the orchestrator delegates to it."\n'
    assert scoped in (tmp_path / ".claude" / "agents" / "qa-tester.md").read_text(encoding="utf-8")
    assert scoped in (tmp_path / ".agents" / "agents" / "qa-tester" / "agent.md").read_text(encoding="utf-8")
    lead = (tmp_path / ".agents" / "agents" / "orchestrator" / "agent.md").read_text(encoding="utf-8")
    assert 'description: "Leads the team"\n' in lead


def test_bom_in_manifest_and_prompt_is_ignored(tmp_path):
    make_source(tmp_path, QA_TOML, {})
    manifest = tmp_path / "agents" / "roles.toml"
    manifest.write_bytes(b"\xef\xbb\xbf" + manifest.read_bytes())
    (tmp_path / "agents" / "qa-tester.md").write_bytes(b"\xef\xbb\xbf# QA\n")

    assert build_agents.main([], root=tmp_path) == 0

    text = (tmp_path / ".claude" / "agents" / "qa-tester.md").read_text(encoding="utf-8")
    assert text.endswith(QA_BANNER + "# QA\n")


def test_non_utf8_hand_written_agent_is_left_alone(tmp_path):
    make_source(tmp_path, QA_TOML, {"qa-tester": "# QA\n"})
    build_agents.main([], root=tmp_path)
    legacy = tmp_path / ".claude" / "agents" / "café-helper.md"
    legacy.write_bytes("---\nname: cafe-helper\n---\n\nCafé notes\n".encode("cp1252"))

    assert build_agents.main(["--check"], root=tmp_path) == 0
    assert build_agents.main([], root=tmp_path) == 0

    assert legacy.exists()


def test_slash_command_is_removed_when_no_role_is_the_main_agent(tmp_path, capsys):
    make_source(tmp_path, QA_TOML + ORCH_TOML, {"qa-tester": "# QA\n", "orchestrator": "# Lead\n"})
    build_agents.main([], root=tmp_path)
    (tmp_path / "agents" / "roles.toml").write_text(QA_TOML, encoding="utf-8")
    (tmp_path / "agents" / "orchestrator.md").unlink()
    capsys.readouterr()

    assert build_agents.main(["--check"], root=tmp_path) == 1
    assert "templates/claude/orchestrate.md" in capsys.readouterr().out
    assert build_agents.main([], root=tmp_path) == 0

    assert not (tmp_path / "templates" / "claude" / "orchestrate.md").exists()
    assert not (tmp_path / ".agents" / "agents" / "orchestrator").exists()
