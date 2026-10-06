---
trigger: always_on
description: "Universal industry-standard naming and nomenclature conventions for all projects"
---

# Universal Naming & Nomenclature Standards

All agents (Orchestrator, Architect, Developer, DevOps) must enforce these industry-standard naming conventions across all generated files, folders, and code artifacts.

## 1. Project & Repository Naming
- **Format**: `PascalCase` with 2 to 3 descriptive words.
- **Examples**: `InvoiceWorkflowAutomation`, `FinancialStatementParser`, `ClientChurnPrediction`.
- **Agent display names**: PascalCase (`FrontendDeveloper`, `UiReviewer`). Agent ids stay kebab-case (`frontend-developer`) because Claude Code and Antigravity require it. Change-type labels are PascalCase too (`Feature`, `Fix`, `Refactor`, `Redesign`, `Transformation`).
- **Prohibited**: Non-descriptive names (`app`, `project1`, `test_repo`), camelCase (`invoiceApp`), or kebab-case (`invoice-app`) unless an external assignment brief strictly mandates it.

## 2. Directory & Package Structure
- **Format**: Lowercase single words or `kebab-case`.
- **Standard Directories**:
  - `src/`: Application source code.
  - `tests/`: Automated unit, integration, and E2E test suites.
  - `docs/`: Living documentation suite.
  - `scripts/`: Operational or deployment helper scripts.

## 3. Code Files & Modules
- **Python**:
  - Files/Modules: `snake_case.py` (e.g., `user_service.py`, `token_auth.py`, `test_parser.py`).
  - Classes: `PascalCase` (e.g., `StatementParser`, `TokenManager`).
  - Functions & Variables: `snake_case` (e.g., `parse_invoice()`, `is_authenticated`).
  - Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT_MS`).
- **TypeScript / JavaScript**:
  - React/UI Components: `PascalCase.tsx` / `PascalCase.jsx` (e.g., `DashboardView.tsx`, `SidebarNav.tsx`).
  - Utilities / Hooks: `camelCase.ts` (e.g., `useAuth.ts`, `formatCurrency.ts`).

## 4. Living Documentation Suite
- Critical root specifications in `docs/` must use `UPPER_SNAKE_CASE.md`:
  - `docs/README.md` (docs index)
  - `docs/PROJECT_MENTAL_MODEL.md`
  - `docs/SPEC.md`
  - `docs/ARCHITECTURE.md`
  - `docs/DECISIONS.md`
  - `docs/TASKS.json`
  - `docs/QA_RESULTS.json`
  - `docs/ADVERSARIAL_REVIEW.md`
  - `docs/FEEDBACK.md`
  - `docs/UI_REVIEW.md` (projects with a UI only)
  - `docs/PROJECT_STATUS.md`
  - `docs/CODEBASE_MAP.md` (existing projects only)
- Root: `README.md` and `CHANGELOG.md`. Projects with a UI also keep `PRODUCT.md` and `DESIGN.md` in the root, in Impeccable's format.

## 5. Git Branches & Commit Messages
- **Branch Naming**: `<type>/<kebab-case-description>`
  - Examples: `feature/invoice-parser`, `bugfix/null-date-error`, `chore/setup-telemetry`.
- **Commit Messages**: Conventional Commits specification:
  - `<type>(<scope>): <clear description in imperative mood>`
  - Examples: `feat(parser): add GAAP balance sheet validation`, `test(qa): add edge case coverage for empty CSV`.
