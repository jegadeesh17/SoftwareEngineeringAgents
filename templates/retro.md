---
retro_format: 1
sea_commit: <commit from ~/.se-agents/source.json, or unknown>
runtime: <claude-code or antigravity>
orchestrator_model: <the model you run on, for example opus>
started: <YYYY-MM-DD>
finished: <YYYY-MM-DD when the project ends; leave empty while in-progress>
project_type: <generic type, for example Streamlit dashboard; never a product name>
existing_code: <yes or no>
ui: <yes or no>
sensitive_data: <yes or no>
deploy: <yes or no>
change_type: <new, Feature, Fix, Refactor, Redesign or Transformation>
milestones_planned: <number>
milestones_accepted: <number>
outcome: <in-progress, completed or abandoned>
---

<!--
Team retro, written by the orchestrator and read by the SoftwareEngineeringAgents maintainers.
Describe the team's behavior, never the product: no product or client names, code, absolute
paths, URLs, emails, secrets or .env values.

Log: one row per event, written when it happens.
  Kind:         went-well, mistake, bug, failure, user-correction, hand-off-gap, environment, conflict
  Severity:     low, medium or high; "-" for went-well
  Likely cause: a role (backend-developer) or a workflow step (Phase 2.4)

Scores, at handover: one row per agent that ran, the orchestrator included. Each score is 1-5 or n/a
and cites log rows or counts as evidence.
  First try:    5 every task passed the first verification; 3 some tasks needed a retry; 1 a task hit the retry limit
  Correctness:  5 no rejected review and no UAT defect traced to the agent; 3 one; 1 repeated, or a defect reached the user twice
  Instructions: 5 no logged deviation; 3 one (wrong file, skipped step, out-of-scope change); 1 repeated
  Hand-off:     5 no hand-off-gap caused by or blocking the agent; 3 one; 1 repeated
-->

## Summary

<!-- At handover: what went well, the top 3 recurring problems, and up to 5 ranked changes to the team, each naming the role or workflow step to change. -->

## Scores

| Agent | Correctness | Instructions | First try | Hand-off | Evidence |
|---|---|---|---|---|---|

## Log

| Date | Phase/task | Agent | Kind | Severity | What happened | Cost | Likely cause | Suggested change |
|---|---|---|---|---|---|---|---|---|
