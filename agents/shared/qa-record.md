### Record the run

Append one entry to `docs/QA_RESULTS.json` (append only; create it as `[]` if missing):

```json
{"task_id": "M1-TASK-01", "attempt": 1, "command": "python -m pytest -q -m \"not slow\"", "exit_code": 0, "summary": "5 passed", "failure_output": ""}
```

- `attempt` is the attempt number from your delegation message.
- `failure_output` holds the last 50 or so lines of output when `exit_code` is not 0.
- Record the real exit code. Never report a pass you did not observe.
- A test that cannot fail is not a test: assert on real outputs.
- The orchestrator re-runs your recorded `command` itself. A pass it cannot reproduce counts as a failed attempt.
