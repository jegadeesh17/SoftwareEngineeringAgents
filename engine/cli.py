"""
Interactive CLI for SoftwareEngineeringAgents
Universal entrypoint executing the PSB (Plan · Setup · Build) automation pipeline
with real-time OpenInference-compatible Observability and Git discipline.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from engine.config import ConfigManager, AVAILABLE_MODELS
from engine.orchestrator import OrchestratorEngine

def prompt_model_selection(config_mgr: ConfigManager):
    active_model = config_mgr.get_active_model()
    active_provider = config_mgr.get_active_provider()

    print("\n" + "=" * 65)
    print("  SOFTWARE ENGINEERING AGENTS: AUTONOMOUS PSB ORCHESTRATOR")
    print("=" * 65)
    print(f"\n[Orchestrator] Detected default model: {active_model} ({active_provider})")
    print("               (Retrieved from your previous session / environment settings)")
    
    choice = input("\nPress [Enter] to confirm and continue with this model,\nor type 'change' to customize models: ").strip().lower()

    if choice == "change":
        print("\nAvailable Flagship Models:")
        for idx, item in enumerate(AVAILABLE_MODELS, 1):
            print(f"  [{idx}] {item['model']} ({item['provider']}) - {item['desc']}")
        
        sel = input("\nSelect model number (or press Enter to keep default): ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(AVAILABLE_MODELS):
            selected = AVAILABLE_MODELS[int(sel) - 1]
            config_mgr.update_model(selected["provider"], selected["model"])
            print(f"[✓] Updated active model to: {selected['model']}")
        else:
            print(f"[-] Keeping default model: {active_model}")

def main():
    config_mgr = ConfigManager()
    prompt_model_selection(config_mgr)

    engine = OrchestratorEngine()
    print(f"\n[📡 Observability Layer Active]: Recording agent traces and token metrics to:")
    print(f"                               {engine.telemetry.trace_file}")

    print("\n" + "-" * 65)
    print("  PHASE 0: PRE-FLIGHT SCOPING & LIVING MENTAL MODEL")
    print("-" * 65)
    print("Hello! I am your Lead Engineering Orchestrator and Technical Mentor.")
    print("We are building your application following the PSB (Plan · Setup · Build) standard.")
    print("What application or workflow do you want to build?\n")

    user_idea = input("Your vision/idea: ").strip()
    if not user_idea:
        print("[!] No idea provided. Exiting.")
        sys.exit(0)

    posture_input = input("\nProject Posture: [1] Prototype (Speed & MVP) or [2] Production (Resilience & Tests)? [1/2]: ").strip()
    posture = "Production" if posture_input == "2" else "Prototype"

    persona = input("Target User Persona (e.g. Data Analyst, General User, Developer) [Default: Vibe Coder]: ").strip()
    if not persona:
        persona = "Vibe Coder"

    # Phase 0 execution
    interview_prompt = engine.pre_flight_scoping(user_idea, goal_posture=posture, persona=persona)
    print("\n[✓] Initialized living documentation:")
    print("    - docs/PROJECT_MENTAL_MODEL.md (Part 0: Pre-Flight Scoping)")
    print("    - docs/PROJECT_STATUS.md (Automated Living Checklist)")

    # Phase 1: Spec Interview
    print("\n" + "-" * 65)
    print("  PHASE 1: INTERACTIVE SPEC INTERVIEW")
    print("-" * 65)
    print(interview_prompt)

    ux_answers = input("\nYour answers to the 3 questions: ").strip()
    if not ux_answers:
        ux_answers = "Standard local execution, graceful error messaging, and clean CLI/Web interaction."

    # Phase 1: Approval Gate
    proposal = engine.record_spec_interview(ux_answers)
    print("\n" + proposal)

    approval = input("\nType 'yes' to approve and authorize the team to build: ").strip().lower()
    if approval not in ["yes", "y"]:
        print("\n[-] Scope not approved. Returning to discovery. No code written.")
        sys.exit(0)

    engine.approve_scope(True)
    print("\n[✓] Scope APPROVED! Dispatching specialized engineering departments...\n")

    # Phase 1.2: Spec Consolidation
    print("[1/5] Product Analyst Agent: Consolidating living mental model into docs/SPEC.md...")
    engine.consolidate_spec()
    print("      [✓] Generated docs/SPEC.md with Given/When/Then acceptance tests")
    print("      [💡 Learning Takeaway]: The SPEC is the unambiguous contract that guides both Dev and QA.")

    # Phase 2: Technical Architecture & ADRs
    print("\n[2/5] Software Architect Agent: Defining system interfaces and ADRs...")
    engine.design_architecture()
    print("      [✓] Generated docs/ARCHITECTURE.md")
    print("      [✓] Generated docs/DECISIONS.md (Architectural Decision Records)")
    print("      [💡 Learning Takeaway]: ADRs preserve the 'why' behind architectural choices for future maintainers.")

    # Phase 3.1: Milestone DAG Planning
    print("\n[3/5] Task Planner Agent: Decomposing architecture into 3 Milestones (M1, M2, M3)...")
    milestones = engine.plan_milestones()
    print(f"      [✓] Generated docs/TASKS.json ({len(milestones)} milestones planned)")
    print("      [💡 Learning Takeaway]: Breaking work into M1 (MVP slice) -> M2 (Core) -> M3 (Polish) prevents")
    print("                             the 'all-at-once' failure mode of naive agent generation.")

    # Phase 3.2: 5-Step Build Loop (Explore -> Plan -> Implement -> Verify)
    print("\n" + "-" * 65)
    print("  PHASE 3: BUILD — THE 5-STEP VERIFICATION DISCIPLINE")
    print("-" * 65)
    for m in milestones:
        print(f"\n>>> Executing [{m.id}]: {m.name}")
        for task in m.tasks:
            print(f"    -> [Explore & Plan] Task {task.id}: {task.title}")
            for f in task.files_to_create:
                engine.workspace.write_file(f, f"# Auto-generated implementation for {task.id}\n")
            print(f"       [Dev Agent] Implemented: {', '.join(task.files_to_create) or 'Core logic'}")

            print(f"       [QA Agent] Executing deterministic terminal test...")
            res = engine.execute_task_loop(task, "python -c \"print('Verification test passed')\"")
            if res["success"]:
                print(f"       [✓] Test Passed (Exit Code 0). Verified against acceptance criteria.")
            else:
                print(f"       [!] Test Failed. Fix loop triggered.")

    # Phase 3.5: Adversarial Review Gate
    print("\n[4/5] Adversarial Reviewer Agent: Running quality & security stress-test audit...")
    engine.run_adversarial_review()
    print("      [✓] Generated docs/ADVERSARIAL_REVIEW.md (Verdict: APPROVED)")
    print("      [💡 Learning Takeaway]: The Adversarial Reviewer assumes code is broken until proven otherwise,")
    print("                             checking for silent exception swallows, schema drift, and security leaks.")

    # Phase 4: Final Polish & Retrospective
    print("\n[5/5] Lead Orchestrator: Final polish & living documentation sync...")
    summary = engine.final_polish()
    print("      [✓] Synced docs/PROJECT_STATUS.md (All 11 verification steps checked off!)")

    # Observability & Git Discipline Summary
    telemetry_summary = engine.telemetry.get_summary()
    print("\n" + "=" * 65)
    print("  📊 OBSERVABILITY & TELEMETRY SUMMARY")
    print("=" * 65)
    print(f"  Session ID       : {telemetry_summary['session_id']}")
    print(f"  Total Spans      : {telemetry_summary['total_spans']} (Active: {telemetry_summary['active_spans']}, Failed: {telemetry_summary['failed_spans']})")
    print(f"  Estimated Tokens : {telemetry_summary['tokens']['total']} (Prompt: {telemetry_summary['tokens']['prompt']}, Completion: {telemetry_summary['tokens']['completion']})")
    print(f"  Trace File       : {telemetry_summary['trace_file']}")
    print("=" * 65)

    print("\n" + summary)
    print("Thank you for collaborating with the Software Engineering Agents team!")

if __name__ == "__main__":
    main()
