---
description: Ground-truth verification rules for QA testing and delivery
globs: ["*"]
always_on: true
---

# QA Verification & Evaluator-Optimizer Protocol

All code authored by the Developer Agent must undergo independent, deterministic verification by the QA Tester Agent before acceptance.

## 1. No Hallucinated Success
- An agent is strictly prohibited from claiming code "works" or is "verified" based on visual inspection or LLM self-evaluation.
- Acceptance requires **real execution** via terminal/subprocess commands (e.g., `pytest`, `npm test`, or script runs).

## 2. The Evaluator-Optimizer Loop
For every task in the backlog:
1. **Developer Agent**: Implements the code change for the specific task.
2. **QA Tester Agent**:
   - Inspects the task acceptance criteria.
   - Writes or updates automated tests.
   - Executes the test command in the terminal.
   - Captures stdout, stderr, and exit codes.
3. **If Tests Fail (Exit Code != 0)**:
   - Provide the raw error output, stack trace, and failing assertions back to the Developer Agent.
   - Increment the attempt counter.
   - Maximum 3 attempts before escalating to the Orchestrator for architectural review.
4. **If Tests Pass (Exit Code == 0)**:
   - Record test logs in `docs/QA_RESULTS.json`.
   - Mark the task as `COMPLETED`.
   - Advance to the next task.
