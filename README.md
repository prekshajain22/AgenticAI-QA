# AgenticAI-QA

Playwright + Pytest BDD automation framework with AI-powered failure analysis, a synchronous Flask test-runner API, and n8n workflow orchestration.

## Tech Stack

Python · Playwright · Pytest-BDD · Flask · ReportLab · Ruff · n8n

---

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install
```

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
pytest -v                                          # all tests
pytest tests/unit/ -v                              # unit tests only
pytest tests/step_definitions/ -v                 # BDD tests only
pytest -m smoke -v                                 # smoke suite
pytest -m regression -v                            # regression suite
pytest -n auto -v                                  # parallel execution
pytest -k "login" -v                               # by name filter
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
├── tests/
│   ├── features/            # Gherkin feature files (login, add_to_cart)
│   ├── step_definitions/    # Pytest-BDD step implementations
│   └── unit/                # Unit tests (data_reader, AI agents)
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

| Symptom                    | Fix                                                                                                  |
| -------------------------- | ---------------------------------------------------------------------------------------------------- |
| `ModuleNotFoundError`      | Activate the virtualenv; run from the project root                                                   |
| Port already in use        | Set `FLASK_PORT=5002` in `.env`                                                                      |
| Playwright browser missing | `playwright install`                                                                                 |
| n8n can't reach Flask      | Flask must be running; `host.containers.internal` resolves the host from inside the podman container |
| Stale `__pycache__`        | `Get-ChildItem -Recurse -Filter __pycache__ \| Remove-Item -Recurse -Force`                          |
