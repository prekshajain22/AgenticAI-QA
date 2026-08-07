# AgenticAI-QA

Playwright + Pytest BDD automation framework with AI-powered failure analysis, a synchronous Flask test-runner API, and n8n workflow orchestration.

## Tech Stack

Python · Playwright · Pytest-BDD · Flask · ReportLab · Ruff · n8n · AutoGen · Gemini · JIRA MCP

---

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install
```

> **JIRA agents also require `uv` (for `uvx mcp-atlassian`):**
>
> ```powershell
> # Windows
> powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
> # macOS / Linux
> curl -LsSf https://astral.sh/uv/install.sh | sh
> ```
>
> See https://docs.astral.sh/uv/getting-started/installation/

Create a `.env` file (all values are optional — defaults shown):

```
BASE_URL=https://www.saucedemo.com
BROWSER=chromium          # chromium | firefox | webkit
HEADLESS=True
SLOW_MO=0
DEFAULT_TIMEOUT=5000
DEFAULT_NAVIGATION_TIMEOUT=10000
FLASK_PORT=5001
```

---

## Running Tests

```powershell
pytest -v                                          # all tests (integration excluded by default)
pytest tests/unit/ -v                              # unit tests only
pytest tests/step_definitions/ -v                 # BDD tests only
pytest -m smoke -v                                 # smoke suite
pytest -m regression -v                            # regression suite
pytest -m integration -s                           # integration tests (requires real credentials)
pytest -n auto -v                                  # parallel execution
pytest -k "login" -v                               # by name filter
```

> Integration tests (`tests/integration/`) hit real external services (JIRA, Gemini).
> They are excluded from the default run via `pytest.ini` `-m "not integration"`.
> Run them explicitly after setting credentials in `.env`.

---

## JIRA AI Agents

The `agents/jira/` package provides AutoGen agents that connect to JIRA via the
[mcp-atlassian](https://github.com/sooperset/mcp-atlassian) MCP server (requires `uv`).

**Required `.env` variables:**

```
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.0-flash   # optional — this is the default
JIRA_URL=https://your-org.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=...
JIRA_PROJECT_KEY=CRED
JIRA_PROJECT_NAME=CreditBank
```

**Run the Bug Analyser:**

```powershell
python -m agents.jira.bug_analyser
```

**Verify MCP connectivity first:**

```powershell
python scripts/check_mcp_connection.py
```

---

## Running the Full Workflow (Flask + n8n)

### 1. Start the Flask API

```powershell
.venv\Scripts\Activate.ps1
python service\test_runner.py
```

The service binds to `0.0.0.0:5001` (port configurable via `FLASK_PORT`).

### 2. Start n8n

```powershell
podman start n8n
```

Open `http://localhost:5678` and import:
`n8n-workflows/QA Test Execution Orchestrator v3.json`

### 3. Trigger via n8n

Click **Execute workflow** — n8n POSTs to `/run-tests`, waits for the synchronous response, runs the AI summary node, then sends the email with the PDF attached.

### 4. Verify manually (without n8n)

```powershell
# Run tests and get full JSON result
$result = (Invoke-WebRequest -Method POST http://localhost:5001/run-tests -UseBasicParsing).Content | ConvertFrom-Json
$result | Select-Object run_id, execution_status, summary

# Download the PDF
Invoke-WebRequest http://localhost:5001/download-report -OutFile QA_Report.pdf -UseBasicParsing
```

---

## Flask API Reference

| Method | Endpoint           | Description                                                |
| ------ | ------------------ | ---------------------------------------------------------- |
| `POST` | `/run-tests`       | Run full pytest suite synchronously; returns complete JSON |
| `GET`  | `/health`          | Liveness probe — returns `{"status": "ok"}`                |
| `GET`  | `/download-report` | Download PDF from the most recent run                      |

`POST /run-tests` blocks until pytest, PDF generation, and AI analysis are all complete. Set the n8n HTTP Request node timeout to at least 600 s (10 min) to match the service's expected run time.

---

## Project Layout

```
agenticai-qa/
├── automation/              # Browser-automation framework
│   ├── actions/             #   Business-level workflows (LoginActions, InventoryActions)
│   ├── components/          #   Reusable UI element wrappers (Button, Label, TextInput)
│   ├── fixtures/            #   Pytest fixtures (browser, pages, data, screenshots)
│   ├── locators/            #   CSS/attribute selectors
│   ├── pages/               #   Page Objects (LoginPage, InventoryPage)
│   └── utils/               #   Helpers (logger, waits, data_reader, assertions)
├── ai/                      # AI failure-analysis agents
│   ├── ai_failure_agent.py  #   Prompt builder (plugs into any LLM)
│   └── report_analysis_agent.py  # Classifies failures, derives root cause
├── service/                 # Flask test-runner API
│   ├── test_runner.py       #   POST /run-tests · GET /health · GET /download-report
│   └── pdf_report_generator.py   # ReportLab PDF builder
├── agents/
│   ├── jira/                # JIRA AutoGen agents
│   │   ├── _client.py       #   Shared Gemini client + MCP server params factory
│   │   └── bug_analyser.py  #   Bug Analyser agent (searches & reports defects)
│   └── ...                  # Other AutoGen agents (ai_failure_agent, etc.)
├── scripts/
│   └── check_mcp_connection.py  # Manual connectivity check for mcp-atlassian
├── tests/
│   ├── features/            # Gherkin feature files (login, add_to_cart)
│   ├── step_definitions/    # Pytest-BDD step implementations
│   ├── unit/                # Fast unit tests (no external services)
│   └── integration/         # Integration tests — excluded from CI by default
├── config/
│   └── settings.py          # Env-var driven config (BASE_URL, BROWSER, HEADLESS, …)
├── test_data/
│   └── users.json           # Test user credentials
├── n8n-workflows/           # n8n workflow JSON files (v1, v2, v3)
├── output/                  # Generated output — gitignored
│   ├── reports/             #   Per-run HTML, JSON, PDF reports
│   ├── logs/                #   flask.log
│   └── screenshots/         #   Failure screenshots
├── .github/workflows/       # CI (GitHub Actions)
├── conftest.py
├── pytest.ini
├── pyproject.toml
└── requirements.txt
```

---

## Code Quality

```powershell
ruff format .    # auto-format
ruff check .     # lint (E, F, I rules)
```

---

## Troubleshooting

| Symptom                        | Fix                                                                                                               |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| `ModuleNotFoundError`          | Activate the virtualenv; run from the project root                                                                |
| Port already in use            | Set `FLASK_PORT=5002` in `.env`                                                                                   |
| Playwright browser missing     | `playwright install`                                                                                              |
| n8n can't reach Flask          | Flask must be running; `host.containers.internal` resolves the host from inside the podman container              |
| Stale `__pycache__`            | `Get-ChildItem -Recurse -Filter __pycache__ \| Remove-Item -Recurse -Force`                                       |
| `uvx: command not found`       | Install `uv`: see https://docs.astral.sh/uv/getting-started/installation/                                         |
| `ModuleNotFoundError: mcp`     | Run `pip install -r requirements.txt` — needs `autogen-ext[mcp]` and `mcp<2.0.0`                                  |
| JIRA `KeyError` / `ValueError` | Set `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN` in `.env`; verify with `python scripts/check_mcp_connection.py` |
