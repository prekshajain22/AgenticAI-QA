# Architecture

## System overview

AgenticAI-QA is a three-layer system:

1. **Automation layer** — Playwright + pytest-BDD tests with Page Object Model
2. **AI agent layer** — autonomous agents for bug analysis, browser execution, and failure analysis
3. **Service layer** — Flask API that wires everything together and exposes it to n8n

---

## Package map

```
agenticai-qa/
├── agents/                     AI agent framework
│   ├── agent_factory.py        AgentFactory — creates AssistantAgent from prompts
│   ├── mcp_config.py           MCPConfig — model clients + MCP server params
│   ├── jira/
│   │   ├── jira_bug_analyser.py   Fetches Jira bugs → smoke test plan
│   │   └── jira_reporter.py       Posts test results back to Jira as comments
│   ├── playwright/
│   │   └── playwright_agent.py    Executes smoke tests in a real browser via MCP
│   ├── pipelines/
│   │   └── jira_playwright.py     3-stage pipeline: Jira → Playwright → Jira update
│   ├── analysis/
│   │   ├── ai_failure_agent.py    Classifies pytest failures + recommends fix (OpenAI)
│   │   └── report_analysis_agent.py  Reads pytest JSON report, calls AIFailureAgent
│   └── prompts/
│       ├── jira_bug_analyst.py    System prompt for JiraBugAnalyser
│       ├── jira_reporter.py       System prompt for JiraReporter
│       └── playwright_automation.py  System prompt for PlaywrightAgent
│
├── automation/                 Browser-automation framework (Page Object Model)
│   ├── actions/                Business workflows — LoginActions, InventoryActions
│   ├── components/             UI wrappers — Button, Label, TextInput, Checkbox, Dropdown
│   ├── fixtures/               Pytest fixtures (browser, pages, actions, data, screenshots)
│   ├── locators/               CSS/data-test selectors
│   ├── pages/                  Page Objects — BasePage, LoginPage, InventoryPage
│   └── utils/                  logger, waits, data_reader, assertions
│
├── service/                    Flask test-runner API
│   ├── test_runner.py          POST /run-tests → pytest → AI analysis → PDF → JSON
│   └── pdf_report_generator.py ReportLab PDF generator
│
├── tests/
│   ├── features/               Gherkin .feature files
│   ├── step_definitions/       pytest-BDD step definitions
│   ├── unit/                   Offline unit tests (no browser, no network)
│   └── integration/            Live agent tests (require Jira + AI keys)
│
├── config/settings.py          All env-var config in one place
├── test_data/users.json        Credential fixtures (SauceDemo users)
├── scripts/                    Diagnostic utilities
│   └── check_mcp_connection.py Verifies Jira MCP connectivity
└── output/                     Generated artefacts (gitignored)
    ├── reports/<run_id>/       result.json · test_report.html · QA_Execution_Report.pdf
    ├── logs/flask.log
    └── screenshots/
```

---

## Pipeline 1 — Jira → Playwright → Jira update

```
JiraBugAnalyser (Jira MCP)
  → reads open bugs, produces smoke test plan
  → emits: HANDOFF TO AUTOMATION

PlaywrightAgent (Playwright MCP)
  → executes each step in a real browser
  → emits: TESTING COMPLETE

JiraReporter (Jira MCP)
  → posts PASS/FAIL comment on each Jira issue
  → emits: JIRA UPDATED
```

Run: `python -m agents.pipelines.jira_playwright`

---

## Pipeline 2 — pytest → AI failure analysis

```
pytest run → output/reports/<run_id>/result.json
  → ReportAnalysisAgent reads JSON
  → AIFailureAgent analyses each failure (OpenAI)
  → combined ai_analysis.json
  → PDF report via service/test_runner.py
```

Run: `python service/test_runner.py` (starts Flask on port 5001)

---

## Configuration

All settings in `config/settings.py`, driven by `.env`.

| Variable             | Default                     | Used by                                       |
| -------------------- | --------------------------- | --------------------------------------------- |
| `BASE_URL`           | `https://www.saucedemo.com` | PlaywrightAgent, page fixtures                |
| `BROWSER`            | `chromium`                  | browser_fixtures                              |
| `HEADLESS`           | `True`                      | browser_fixtures                              |
| `OPENROUTER_API_KEY` | —                           | MCPConfig.openrouter_client()                 |
| `GEMINI_API_KEY`     | —                           | MCPConfig.gemini_client() (needs AIza... key) |
| `JIRA_URL`           | —                           | JiraBugAnalyser, JiraReporter                 |
| `OPENAI_API_KEY`     | —                           | AIFailureAgent                                |
| `FLASK_SECRET`       | _(empty)_                   | service/test_runner.py                        |
