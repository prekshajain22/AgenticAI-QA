# Architecture

## Overview

AgenticAI-QA is a three-layer system:

1. **Automation layer** — Playwright + Pytest-BDD tests organised with Page Object Model
2. **AI layer** — failure analysis agents that classify errors and generate diagnostic prompts
3. **Service layer** — synchronous Flask API that wires everything together and exposes it to n8n

```
n8n workflow
    │
    │  POST /run-tests
    ▼
┌─────────────────────────────────┐
│  service/test_runner.py          │  Flask (port 5001)
│                                  │
│  1. subprocess: pytest           │
│  2. parse result.json            │
│  3. ReportAnalysisAgent          │  ◄─── ai/report_analysis_agent.py
│  4. generate_pdf()               │  ◄─── service/pdf_report_generator.py
│  5. return JSON payload          │
└─────────────────────────────────┘
    │
    │  200 OK  { execution_status, summary,
    │            failed_tests[].ai_analysis,
    │            root_cause, pdf_report }
    ▼
n8n: Format AI Summary → Send Email (PDF attached)
```

---

## Package Map

```
agenticai-qa/
├── automation/          Browser-automation framework (Page Object Model)
│   ├── actions/         Business workflows — LoginActions, InventoryActions
│   ├── components/      UI wrappers — Button, Label, TextInput, Checkbox, Dropdown
│   ├── fixtures/        Pytest fixtures
│   │   ├── browser_fixtures.py   Playwright page fixture (BROWSER env var respected)
│   │   ├── pages_fixtures.py     LoginPage / InventoryPage fixtures
│   │   ├── action_fixtures.py    LoginActions / InventoryActions fixtures
│   │   ├── data_fixtures.py      users.json reader
│   │   └── screenshot_fixtures.py  Auto-capture on failure → output/screenshots/
│   ├── locators/        CSS/data-test selectors for each page
│   ├── pages/           Page Objects (BasePage, LoginPage, InventoryPage)
│   └── utils/           Cross-cutting helpers
│       ├── logger.py    Structured logger
│       ├── waits.py     Explicit-wait helpers
│       ├── data_reader.py  JSON fixture loader (project-root relative paths)
│       └── assertions.py   Custom assertion helpers
│
├── ai/                  Failure-analysis pipeline
│   ├── ai_failure_agent.py       Builds diagnostic prompts per failure
│   │                             (plugs in to any LLM — currently returns prompt string)
│   └── report_analysis_agent.py  Orchestrates full report analysis:
│                                   • execution_summary()
│                                   • failed_tests() + clean_error()
│                                   • classify_failure()  → error category
│                                   • analyse_failure()   → human recommendation
│                                   • root_cause()        → top-level diagnosis
│                                   • generate_analysis() → full dict wired into service
│
├── service/             Flask test-runner API
│   ├── test_runner.py   Single synchronous endpoint:
│   │                     POST /run-tests → pytest → AI → PDF → JSON
│   │                     GET  /health   → liveness probe
│   │                     GET  /download-report → latest PDF
│   └── pdf_report_generator.py  ReportLab PDF: status, summary,
│                                 execution trace, screenshots, AI analysis
│
├── tests/
│   ├── features/        Gherkin (.feature files)
│   ├── step_definitions/ Pytest-BDD step definitions (shared + per-feature)
│   └── unit/            Pure-Python unit tests (no browser, no network)
│       ├── test_ai_agents.py     AIFailureAgent + ReportAnalysisAgent logic
│       └── test_data_reader.py   read_json contract
│
├── config/settings.py   All env-var config in one place
│                         BASE_URL · BROWSER · HEADLESS · SLOW_MO
│                         DEFAULT_TIMEOUT · DEFAULT_NAVIGATION_TIMEOUT
│                         FRAMEWORK · ENVIRONMENT
│
├── test_data/users.json  Credential fixtures for Sauce Demo
├── n8n-workflows/        n8n workflow JSON (v1 basic, v2 Jira, v3 sync+AI)
└── output/               All generated artefacts (gitignored)
    ├── reports/<run_id>/ result.json · test_report.html · QA_Execution_Report.pdf
    ├── logs/flask.log
    └── screenshots/
```

---

## Data Flow — POST /run-tests

```
┌─────────────────────────────────────────────────────────────────────┐
│ test_runner.run_tests()                                              │
│                                                                      │
│  subprocess.run(pytest)                                              │
│      ├─ conftest.py loads automation.fixtures.*                      │
│      ├─ browser_fixtures → Playwright page (BROWSER env var)         │
│      ├─ pages_fixtures   → LoginPage / InventoryPage                 │
│      ├─ action_fixtures  → LoginActions / InventoryActions           │
│      ├─ data_fixtures    → test_data/users.json                      │
│      └─ step_definitions → BDD steps → page.* calls                 │
│                                                                      │
│  result_file = output/reports/<run_id>/result.json                   │
│  html_report = output/reports/<run_id>/test_report.html             │
│                                                                      │
│  ReportAnalysisAgent(result_file)                                    │
│      └─ generate_analysis()                                          │
│           ├─ for each failure: AIFailureAgent.analyse()              │
│           ├─ classify_failure()  → "Automation/Test Design Issue"    │
│           ├─ analyse_failure()   → human recommendation              │
│           └─ root_cause()        → top-level diagnosis string        │
│                                                                      │
│  generate_pdf(payload, pdf_path, project_root=PROJECT_ROOT)          │
│      └─ output/reports/<run_id>/QA_Execution_Report.pdf              │
│                                                                      │
│  return 200 JSON payload                                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## n8n Workflow (v3)

```
Manual Trigger
    │
    ▼
Run Tests  (POST /run-tests, timeout 600s)
    │  { execution_status, summary, failed_tests[].ai_analysis, root_cause, ... }
    ▼
Format AI Summary  (Code node)
    │  { pass_rate, ai_summary (joined per-failure analysis), ... }
    ▼
Execution Passed?  (IF execution_status == PASSED)
    ├── TRUE  → Download QA Report (GET /download-report) → Send Email
    └── FALSE → Prepare Jira Payload
                    └─ Check Existing Bug → bug_exists?
                         ├── YES → Mock Update Jira → Download QA Report → Send Email
                         └── NO  → Mock Create Jira → Download QA Report → Send Email
```

---

## Configuration

All runtime settings live in `config/settings.py` and are driven by environment variables (loaded from `.env` via `python-dotenv`).

| Variable                     | Default                     | Used by                             |
| ---------------------------- | --------------------------- | ----------------------------------- |
| `BASE_URL`                   | `https://www.saucedemo.com` | pages (goto)                        |
| `BROWSER`                    | `chromium`                  | browser_fixtures (launch)           |
| `HEADLESS`                   | `True`                      | browser_fixtures                    |
| `SLOW_MO`                    | `0`                         | browser_fixtures                    |
| `DEFAULT_TIMEOUT`            | `5000`                      | page.set_default_timeout            |
| `DEFAULT_NAVIGATION_TIMEOUT` | `10000`                     | page.set_default_navigation_timeout |
| `FLASK_PORT`                 | `5001`                      | service/test_runner.py              |
| `FLASK_SECRET`               | _(empty — check disabled)_  | service/test_runner.py (auth)       |

---

## Adding a New Test

1. Add a scenario to `tests/features/<feature>.feature`
2. Implement any new steps in `tests/step_definitions/shared_steps.py` (or a feature-specific file)
3. Add any new locators to `automation/locators/`
4. Implement page actions in `automation/pages/` and business workflows in `automation/actions/`
5. Run `pytest -v` to verify

## Adding a New AI Analysis Rule

Edit `ai/report_analysis_agent.py`:

- `classify_failure(error)` — add a new `if` branch returning a category string
- `analyse_failure(error)` — add a recommendation for the new pattern

No changes to `service/test_runner.py` are needed — it calls `generate_analysis()` which picks up new rules automatically.
