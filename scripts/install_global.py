"""
Global Installer for SoftwareEngineeringAgents
Installs the generated agent team so it works in any project folder:
1. Claude Code sub-agents   -> ~/.claude/agents/<role>.md
2. Claude Code /orchestrate -> ~/.claude/commands/orchestrate.md
3. Antigravity agents       -> ~/.gemini/config/agents/<role>/agent.md
4. Antigravity global rule 'nomenclature-standards.md' (opt-in via --global-rules)

Existing files that differ from the generated ones are kept unless --force is passed.
Nothing in your home directory is ever deleted.
"""

import argparse
import filecmp
import shutil
import sys
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from engine import build_agents  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def install_file(src: Path, dst: Path, force: bool) -> bool:
    """Copy src to dst, refusing to clobber a customized dst unless force is set."""
    if dst.exists() and not force and not filecmp.cmp(src, dst, shallow=False):
        print(f"      [!] Skipped: {dst} exists and differs from the generated file (re-run with --force to overwrite)")
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"      [OK] Installed: {dst}")
    return True


def main(argv: Optional[List[str]] = None, home: Optional[Path] = None, root: Optional[Path] = None) -> int:
    parser = argparse.ArgumentParser(description="Install the SoftwareEngineeringAgents team globally")
    parser.add_argument("--force", action="store_true", help="overwrite existing files that differ from the generated ones")
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

    print("\n[1/4] Claude Code sub-agents...")
    for src in sorted((root / ".claude" / "agents").glob("*.md")):
        install_file(src, user_home / ".claude" / "agents" / src.name, args.force)

    print("\n[2/4] Claude Code /orchestrate command...")
    install_file(root / "templates" / "claude" / "orchestrate.md",
                 user_home / ".claude" / "commands" / "orchestrate.md", args.force)

    print("\n[3/4] Antigravity agents...")
    for src in sorted((root / ".agents" / "agents").glob("*/agent.md")):
        install_file(src, user_home / ".gemini" / "config" / "agents" / src.parent.name / "agent.md", args.force)
    old_skill = user_home / ".gemini" / "config" / "skills" / "orchestrator"
    if old_skill.exists():
        print(f"      [!] Found the old 'orchestrator' skill at {old_skill}.")
        print("          The orchestrator agent replaces it; delete that folder to avoid two orchestrators.")

    print("\n[4/4] Antigravity global naming rule...")
    if not args.global_rules:
        print("      [-] Not installed: this rule applies to every project (re-run with --global-rules to install).")
    else:
        install_file(root / ".agents" / "rules" / "nomenclature-standards.md",
                     user_home / ".gemini" / "config" / "rules" / "nomenclature-standards.md", args.force)

    print("\n" + "=" * 65)
    print("  INSTALLATION COMPLETE")
    print("=" * 65)
    print("Start the team in any project folder:")
    print("  Claude Code:  run 'claude', then type /orchestrate")
    print("  Antigravity:  run 'agy --agent orchestrator'")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
