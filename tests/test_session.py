import sys
from pathlib import Path
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.orchestrator import OrchestratorEngine

def test_full_session(tmp_path, monkeypatch):
    print("\n--- Starting E2E Session Test ---")
    monkeypatch.chdir(tmp_path)
    eng = OrchestratorEngine(workspace_dir=tmp_path)

    # Phase 0: Pre-flight scoping
    prompt = eng.pre_flight_scoping(
        "Financial Statement Parser",
        goal_posture="Production",
        persona="Financial Analyst"
    )
    assert eng.state.status_checklist["phase_0_scoping"] is True
    print("[✓] Phase 0 Pre-Flight Scoping verified.")

    # Phase 1: Spec interview & approval
    proposal = eng.record_spec_interview(
        "User uploads PDF/CSV, balance sheet extracted, validated with GAAP rules."
    )
    assert eng.state.status_checklist["phase_1_interview"] is True
    approved = eng.approve_scope(True)
    assert approved is True
    print("[✓] Phase 1 Spec Interview & Approval verified.")

    # Phase 1.2: Spec consolidation
    eng.consolidate_spec()
    assert eng.state.status_checklist["phase_1_spec"] is True
    print("[✓] Phase 1.2 docs/SPEC.md consolidated.")

    # Phase 2: Architecture & ADRs
    eng.design_architecture()
    assert eng.state.status_checklist["phase_2_architecture"] is True
    assert eng.state.status_checklist["phase_2_decisions"] is True
    print("[✓] Phase 2 docs/ARCHITECTURE.md & docs/DECISIONS.md verified.")

    # Phase 3: Milestone Planning
    milestones = eng.plan_milestones()
    assert len(milestones) == 3
    assert eng.state.status_checklist["phase_3_planning"] is True
    print(f"[✓] Phase 3.1 Milestone Planning verified ({len(milestones)} milestones).")

    # Phase 3.2: Milestone execution with real terminal tests
    for m in milestones:
        for t in m.tasks:
            for f in t.files_to_create:
                eng.workspace.write_file(f, f"# Auto-generated module for {t.id}\n")
            res = eng.execute_task_loop(t, "python --version")
            assert res["success"] is True
    print("[✓] Phase 3.2 5-Step Build & Terminal Verification loop passed.")

    # Phase 3.5: Adversarial Review
    eng.run_adversarial_review()
    assert eng.state.adversarial_verdict == "APPROVED"
    assert eng.state.status_checklist["phase_3_adversarial"] is True
    print("[✓] Phase 3.5 docs/ADVERSARIAL_REVIEW.md verified.")

    # Phase 4: Final Polish
    summary = eng.final_polish()
    assert eng.state.status_checklist["phase_4_polish"] is True
    print("[✓] Phase 4 Final Polish & Retrospective verified.")

    # Observability & Trace audit
    telemetry = eng.telemetry.get_summary()
    assert telemetry["total_spans"] >= 7
    assert telemetry["tokens"]["total"] > 0
    print("\n--- Observability Telemetry Verified ---")
    print(f"Total Spans Tracked : {telemetry['total_spans']}")
    print(f"Total Tokens Tracked: {telemetry['tokens']['total']}")
    print(f"Trace File Path     : {telemetry['trace_file']}")

    # Verify living documents created
    for doc in [
        "docs/PROJECT_MENTAL_MODEL.md",
        "docs/SPEC.md",
        "docs/ARCHITECTURE.md",
        "docs/DECISIONS.md",
        "docs/TASKS.json",
        "docs/ADVERSARIAL_REVIEW.md",
        "docs/PROJECT_STATUS.md"
    ]:
        content = eng.workspace.read_file(doc)
        assert content is not None, f"Missing document: {doc}"
    print("[✓] All 7 Living Documents created and verified on disk.")
