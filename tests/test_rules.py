from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
RULES = sorted((ROOT / ".agents" / "rules").glob("*.md"))
# Antigravity silently discards rules without a valid trigger (https://antigravity.google/docs/rules/)
TRIGGERS = {"always_on", "model_decision", "glob", "manual"}


def frontmatter(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---", f"{path.name}: missing frontmatter"
    end = lines.index("---", 1)
    fields = {}
    for line in lines[1:end]:
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


@pytest.mark.parametrize("rule", RULES, ids=lambda p: p.name)
def test_rule_frontmatter_matches_antigravity_format(rule):
    fields = frontmatter(rule)

    assert set(fields) <= {"trigger", "description", "globs", "glob"}, f"unknown fields: {sorted(fields)}"
    assert fields.get("trigger") in TRIGGERS
    if fields["trigger"] == "model_decision":
        assert fields.get("description")
    if fields["trigger"] == "glob":
        assert fields.get("globs") or fields.get("glob")
    for key in ("globs", "glob"):
        # A comma-separated string, never a YAML list
        assert not fields.get(key, "").startswith("["), f"{key} must be a string"
