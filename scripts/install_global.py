"""
Global Installer for SoftwareEngineeringAgents
Installs the generated agent team so it works in any project folder:
1. Claude Code sub-agents   -> ~/.claude/agents/<role>.md
2. Claude Code /orchestrate -> ~/.claude/commands/orchestrate.md
3. Antigravity agents       -> ~/.gemini/config/agents/<role>/agent.md
4. Antigravity global rule 'nomenclature-standards.md' (opt-in via --global-rules)

Files this installer wrote before are updated. Files with your own changes are kept
unless --force is passed. Nothing in your home directory is ever deleted.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from engine import build_agents  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Records what was installed, so a later run can tell our own files from the user's edits
MANIFEST_PATH = Path(".se-agents") / "installed.json"
# Content hashes (LF-normalized) of files written by earlier installer versions; safe to replace
LEGACY_HASHES = {
    ".claude/commands/orchestrate.md": {"95aa56d8ff3899f7c54a24cacc2e92791362e3269ee55e4b1143f2c3e6842baf"},
}
RULE_SOURCE = Path(".agents") / "rules" / "nomenclature-standards.md"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_normalized(path: Path) -> Optional[str]:
    try:
        return build_agents.normalize_newlines(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return None


def _load_manifest(home: Path) -> Dict[str, str]:
    try:
        return json.loads((home / MANIFEST_PATH).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_manifest(home: Path, manifest: Dict[str, str]) -> None:
    path = home / MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def install_text(content: str, home: Path, rel: Path, force: bool, manifest: Dict[str, str]) -> bool:
    """Write content to home/rel with LF endings, unless the existing file holds the user's own changes."""
    dst = home / rel
    key = rel.as_posix()
    if dst.exists() and not force:
        current = _read_normalized(dst)
        ours = current is not None and (
            current == content
            or _sha256(current) == manifest.get(key)
            or _sha256(current) in LEGACY_HASHES.get(key, set())
        )
        if not ours:
            print(f"      [!] Skipped: {dst} has your own changes (re-run with --force to overwrite)")
            return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8", newline="\n")
    manifest[key] = _sha256(content)
    print(f"      [OK] Installed: {dst}")
    return True


def _home_path(generated: Path) -> Path:
    """Where a generated repo file is installed, relative to the home directory."""
    if generated == build_agents.CLAUDE_COMMAND_PATH:
        return Path(".claude") / "commands" / "orchestrate.md"
    if generated.parent == build_agents.CLAUDE_AGENTS_DIR:
        return Path(".claude") / "agents" / generated.name
    return Path(".gemini") / "config" / "agents" / generated.parent.name / "agent.md"


def main(argv: Optional[List[str]] = None, home: Optional[Path] = None, root: Optional[Path] = None) -> int:
    parser = argparse.ArgumentParser(description="Install the SoftwareEngineeringAgents team globally")
    parser.add_argument("--force", action="store_true", help="overwrite files that have your own changes")
    parser.add_argument("--global-rules", action="store_true",
                        help="also install the always-on nomenclature rule for every Antigravity project")
    args = parser.parse_args(argv)

    root = root or REPO_ROOT
    user_home = home or Path.home()

    print("=" * 65)
    print("  SOFTWARE ENGINEERING AGENTS: GLOBAL INSTALLER")
    print("=" * 65)

    if build_agents.main(["--check"], root=root) != 0:
        print("\n[!] Nothing installed: generated agent files are out of date with agents/.")
        print("    Run: python -m engine.build_agents")
        return 1

    # Install from the generator's output, not the checkout's bytes, so files are always LF
    outputs = build_agents.build_outputs(build_agents.load_roles(root / build_agents.SOURCE_DIR))
    installs = {_home_path(rel): content for rel, content in outputs.items()}
    manifest = _load_manifest(user_home)
    results = []

    sections = [
        ("[1/4] Claude Code sub-agents...", lambda rel: rel.parent == Path(".claude") / "agents"),
        ("[2/4] Claude Code /orchestrate command...", lambda rel: rel.parent == Path(".claude") / "commands"),
        ("[3/4] Antigravity agents...", lambda rel: rel.parts[:3] == (".gemini", "config", "agents")),
    ]
    for title, belongs in sections:
        print(f"\n{title}")
        for rel in sorted(r for r in installs if belongs(r)):
            results.append(install_text(installs[rel], user_home, rel, args.force, manifest))

    old_skill = user_home / ".gemini" / "config" / "skills" / "orchestrator"
    if old_skill.exists():
        print(f"      [!] Found the old 'orchestrator' skill at {old_skill}.")
        print("          The orchestrator agent replaces it; delete that folder to avoid two orchestrators.")

    print("\n[4/4] Antigravity global naming rule...")
    if not args.global_rules:
        print("      [-] Not installed: this rule applies to every project (re-run with --global-rules to install).")
    else:
        rule = build_agents.normalize_newlines((root / RULE_SOURCE).read_text(encoding="utf-8"))
        results.append(install_text(rule, user_home, Path(".gemini") / "config" / "rules" / RULE_SOURCE.name,
                                    args.force, manifest))

    _save_manifest(user_home, manifest)

    skipped = results.count(False)
    print("\n" + "=" * 65)
    if skipped:
        print(f"  INSTALLATION INCOMPLETE: {skipped} file(s) skipped because they have your own changes.")
        print("  Re-run with --force to overwrite them.")
        print("=" * 65)
        return 1
    print("  INSTALLATION COMPLETE")
    print("=" * 65)
    print("Start the team in any project folder:")
    print("  Claude Code:  run 'claude', then type /orchestrate")
    print("  Antigravity:  run 'agy --agent orchestrator'")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
