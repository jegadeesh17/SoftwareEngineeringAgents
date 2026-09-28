"""
Global Installer for SoftwareEngineeringAgents
Installs:
1. Global Terminal CLI: 'orchestrate' and 'se-agents' via pip
2. Claude Code Global Slash Command: /orchestrate (in ~/.claude/commands/)
3. Antigravity Global Skill: 'orchestrator' (in ~/.gemini/config/skills/)
4. Antigravity Global Rule: 'nomenclature-standards.md' (in ~/.gemini/config/rules/), opt-in via --global-rules

Existing files that differ from the templates are kept unless --force is passed.
"""

import argparse
import filecmp
import sys
import shutil
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def install_file(src: Path, dst: Path, force: bool) -> bool:
    """Copy src to dst, refusing to clobber a customized dst unless force is set."""
    if dst.exists() and not force and not filecmp.cmp(src, dst, shallow=False):
        print(f"      [!] Skipped: {dst} exists and differs from the template (re-run with --force to overwrite)")
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"      [OK] Installed to: {dst}")
    return True

def main(argv=None, home: Path = None):
    parser = argparse.ArgumentParser(description="Install SoftwareEngineeringAgents globally")
    parser.add_argument("--no-pip", action="store_true", help="skip 'pip install -e' of the CLI")
    parser.add_argument("--force", action="store_true", help="overwrite existing files that differ from the templates")
    parser.add_argument("--global-rules", action="store_true",
                        help="also install the always-on nomenclature rule for every Antigravity project")
    args = parser.parse_args(argv)

    root_dir = Path(__file__).parent.parent
    user_home = home or Path.home()

    print("=" * 65)
    print("  SOFTWARE ENGINEERING AGENTS: GLOBAL INSTALLER")
    print("=" * 65)

    # 1. Install CLI command globally
    print("\n[1/4] Installing global terminal CLI ('orchestrate' and 'se-agents')...")
    if args.no_pip:
        print("      [-] Skipped (--no-pip).")
    else:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(root_dir)], check=True)
            print("      [OK] Successfully registered 'orchestrate' command in Python PATH.")
        except Exception as e:
            print(f"      [!] Warning: pip install failed: {e}")

    # 2. Install Claude Code slash command
    print("\n[2/4] Installing Claude Code slash command (/orchestrate)...")
    claude_src = root_dir / "templates" / "claude" / "orchestrate.md"
    claude_dst = user_home / ".claude" / "commands" / "orchestrate.md"
    if claude_src.exists():
        if install_file(claude_src, claude_dst, args.force):
            print("          Usage in Claude Code: Type '/orchestrate' in any folder!")
    else:
        print("      [!] Could not find templates/claude/orchestrate.md")

    # 3. Install Antigravity Global Skill
    print("\n[3/4] Installing Antigravity global skill ('orchestrator')...")
    agy_skill_src = root_dir / "templates" / "antigravity" / "skills" / "orchestrator" / "SKILL.md"
    agy_skill_dst = user_home / ".gemini" / "config" / "skills" / "orchestrator" / "SKILL.md"
    if agy_skill_src.exists():
        if install_file(agy_skill_src, agy_skill_dst, args.force):
            print("          Usage in Antigravity: The 'orchestrator' skill is now active globally!")

    # 4. Install Antigravity Global Rule for Nomenclature Standards
    print("\n[4/4] Installing Antigravity global rule ('nomenclature-standards.md')...")
    rule_src = root_dir / ".agents" / "rules" / "nomenclature-standards.md"
    rule_dst = user_home / ".gemini" / "config" / "rules" / "nomenclature-standards.md"
    if not args.global_rules:
        print("      [-] Skipped: this rule is always-on for every project (re-run with --global-rules to install).")
    elif rule_src.exists():
        if install_file(rule_src, rule_dst, args.force):
            print("          Nomenclature standards are now enforced across all projects!")

    print("\n" + "=" * 65)
    print("  INSTALLATION COMPLETE!")
    print("=" * 65)
    print("You can now trigger your Software Engineering Agents anywhere:")
    print("  1. In any Terminal:   run 'orchestrate'")
    print("  2. In Claude Code:     type '/orchestrate'")
    print("  3. In Antigravity CLI: run 'agy' (orchestrator skill auto-discovered)")
    print("=" * 65)

if __name__ == "__main__":
    main()
