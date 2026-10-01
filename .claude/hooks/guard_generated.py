"""PreToolUse: block hand-edits to generated agent files. Edit agents/ then run engine.build_agents."""
import json, os, sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
root = os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
f = (data.get("tool_input") or {}).get("file_path") or ""
rel = os.path.relpath(os.path.abspath(f), root).replace("\\", "/")
parts = rel.split("/")

generated = False
if rel == "templates/claude/orchestrate.md":
    generated = True
elif len(parts) == 3 and parts[:2] == [".claude", "agents"] and parts[2].endswith(".md"):
    generated = os.path.isfile(os.path.join(root, "agents", parts[2]))  # hand-written helpers stay editable
elif len(parts) == 4 and parts[:2] == [".agents", "agents"] and parts[3] == "agent.md":
    generated = os.path.isfile(os.path.join(root, "agents", parts[2] + ".md"))

if generated:
    print(f"Blocked: {rel} is generated. Edit agents/roles.toml or agents/<role>.md, "
          "then run `python -m engine.build_agents`.", file=sys.stderr)
    sys.exit(2)
