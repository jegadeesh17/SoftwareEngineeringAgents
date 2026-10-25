import json

from engine import usage


def _assistant(request_id, ts, cache_read, output, skill=None, read=None, model="claude-opus-5-5"):
    content = [{"type": "tool_use", "id": f"t-{request_id}", "name": "Read", "input": {"file_path": read}}] if read else []
    entry = {"type": "assistant", "requestId": request_id, "timestamp": ts,
             "message": {"model": model, "content": content,
                         "usage": {"input_tokens": 2, "cache_read_input_tokens": cache_read,
                                   "cache_creation_input_tokens": 1000, "output_tokens": output}}}
    if skill:
        entry["attributionSkill"] = skill
    return json.dumps(entry)


def _write(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _project(tmp_path):
    project = tmp_path / "work" / "My App"
    project.mkdir(parents=True)
    claude_home = tmp_path / "claude"
    folder = claude_home / "projects" / usage.project_slug(project).swapcase()
    _write(folder / "s1.jsonl", [
        json.dumps({"type": "user", "timestamp": "2026-10-01T09:00:00Z", "message": {"content": "hi"}}),
        _assistant("r0", "2026-09-30T09:00:00Z", 500_000, 9, skill="orchestrate"),
        _assistant("r1", "2026-10-01T09:00:01Z", 9_000, 100, skill="orchestrate",
                   read="C:\\work\\My App\\docs\\ARCHITECTURE.md"),
        _assistant("r1", "2026-10-01T09:00:01Z", 9_000, 100),
        _assistant("r2", "2026-10-01T09:00:02Z", 29_000, 300, read="/work/My App/src/app.py"),
        _assistant("r3", "2026-10-01T09:00:03Z", 0, 0, model="<synthetic>"),
    ])
    _write(folder / "s1" / "subagents" / "agent-a1.jsonl", [
        _assistant("q1", "2026-10-01T10:00:00Z", 4_000, 50, read="C:/work/My App/docs/ARCHITECTURE.md"),
    ])
    (folder / "s1" / "subagents" / "agent-a1.meta.json").write_text(json.dumps({"agentType": "qa-tester"}),
                                                                      encoding="utf-8")
    _write(folder / "s2.jsonl", [_assistant("p1", "2026-10-02T09:00:00Z", 1_000, 10)])
    return project, claude_home


def test_slug_replaces_every_non_alphanumeric_character(tmp_path):
    slug = usage.project_slug(tmp_path / "My App")

    assert slug.endswith("-My-App")
    assert all(ch.isalnum() or ch == "-" for ch in slug)


def test_usage_counts_each_request_once_by_agent_and_since(tmp_path):
    project, claude_home = _project(tmp_path)

    report = usage.collect(project, claude_home, since="2026-10-01")

    orchestrator = report.agents["orchestrator"]
    assert (orchestrator.runs, orchestrator.turns) == (1, 2)
    assert orchestrator.input_tokens == (2 + 9_000 + 1000) + (2 + 29_000 + 1000)
    assert orchestrator.output_tokens == 400
    assert orchestrator.peak_context == 30_002
    qa = report.agents["qa-tester"]
    assert (qa.runs, qa.turns, qa.input_tokens) == (1, 1, 5_002)
    assert report.agents["main (other)"].turns == 1
    assert report.doc_reads == {"ARCHITECTURE.md": 2}


def test_rendered_table_has_totals_and_doc_names_only(tmp_path):
    project, claude_home = _project(tmp_path)

    text = usage.render(usage.collect(project, claude_home, since="2026-10-01"))

    assert text.splitlines()[0].startswith("| Agent | Runs | Turns | Turns/run |")
    assert "| **Total** | 3 | 4 |" in text
    assert "Most re-read docs: ARCHITECTURE.md ×2" in text
    assert "My App" not in text


def test_cli_reports_a_project_without_transcripts(tmp_path, capsys):
    status = usage.main([str(tmp_path / "none"), "--claude-home", str(tmp_path / "claude")])

    assert status == 0
    assert "no Claude Code transcripts found" in capsys.readouterr().out
