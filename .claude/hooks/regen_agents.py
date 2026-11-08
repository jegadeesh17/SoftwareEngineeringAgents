"""PostToolUse: regenerate agent files after editing their source (agents/*.md, agents/roles.toml, or a team file the plugin copies)."""
import json, os, subprocess, sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
root = os.path.abspath(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd())
f = (data.get("tool_input") or {}).get("file_path") or ""
rel = os.path.relpath(os.path.abspath(f), root).replace("\\", "/")
TEAM_FILES = ("templates/retro.md", "templates/doc-templates.md", "engine/usage.py")  # copied into plugin/team/
if not (rel == "agents/roles.toml" or rel in TEAM_FILES or (rel.startswith("agents/") and rel.endswith(".md"))):
    sys.exit(0)

r = subprocess.run([sys.executable, "-m", "engine.build_agents"], cwd=root, capture_output=True, text=True, timeout=60)
if r.returncode != 0:
    print("engine.build_agents failed:\n" + (r.stderr or r.stdout), file=sys.stderr)
    sys.exit(2)
