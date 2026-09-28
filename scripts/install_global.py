"""
Global Installer for SoftwareEngineeringAgents
Installs:
1. Global Terminal CLI: 'orchestrate' and 'se-agents' via pip
2. Claude Code Global Slash Command: /orchestrate (in ~/.claude/commands/)
3. Antigravity Global Skill: 'orchestrator' (in ~/.gemini/config/skills/)
4. Antigravity Global Rule: 'nomenclature-standards.md' (in ~/.gemini/config/rules/)
"""

import sys
import shutil
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def main():
    root_dir = Path(__file__).parent.parent
    user_home = Path.home()

    print("=" * 65)
    print("  SOFTWARE ENGINEERING AGENTS: GLOBAL INSTALLER")
    print("=" * 65)

    # 1. Install CLI command globally
    print("\n[1/4] Installing global terminal CLI ('orchestrate' and 'se-agents')...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(root_dir)], check=True)
        print("      [OK] Successfully registered 'orchestrate' command in Python PATH.")
    except Exception as e:
        print(f"      [!] Warning: pip install failed: {e}")

    # 2. Install Claude Code slash command
    print("\n[2/4] Installing Claude Code slash command (/orchestrate)...")
    claude_cmd_dir = user_home / ".claude" / "commands"
    claude_cmd_dir.mkdir(parents=True, exist_ok=True)
    claude_src = root_dir / "templates" / "claude" / "orchestrate.md"
    claude_dst = claude_cmd_dir / "orchestrate.md"
    if claude_src.exists():
        shutil.copy2(claude_src, claude_dst)
        print(f"      [OK] Installed to: {claude_dst}")
        print("          Usage in Claude Code: Type '/orchestrate' in any folder!")
    else:
        print("      [!] Could not find templates/claude/orchestrate.md")

    # 3. Install Antigravity Global Skill
    print("\n[3/4] Installing Antigravity global skill ('orchestrator')...")
    agy_skills_dir = user_home / ".gemini" / "config" / "skills" / "orchestrator"
    agy_skills_dir.mkdir(parents=True, exist_ok=True)
    agy_skill_src = root_dir / "templates" / "antigravity" / "skills" / "orchestrator" / "SKILL.md"
    agy_skill_dst = agy_skills_dir / "SKILL.md"
    if agy_skill_src.exists():
        shutil.copy2(agy_skill_src, agy_skill_dst)
        print(f"      [OK] Installed to: {agy_skill_dst}")
        print("          Usage in Antigravity: The 'orchestrator' skill is now active globally!")

    # 4. Install Antigravity Global Rule for Nomenclature Standards
    print("\n[4/4] Installing Antigravity global rule ('nomenclature-standards.md')...")
    agy_rules_dir = user_home / ".gemini" / "config" / "rules"
    agy_rules_dir.mkdir(parents=True, exist_ok=True)
    rule_src = root_dir / ".agents" / "rules" / "nomenclature-standards.md"
    rule_dst = agy_rules_dir / "nomenclature-standards.md"
    if rule_src.exists():
        shutil.copy2(rule_src, rule_dst)
        print(f"      [OK] Installed to: {rule_dst}")
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
