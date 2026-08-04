# QA Automation Lab

## Overview

Playwright + Pytest BDD automation framework using Page Object Model (POM).

## Tech Stack

- Python · Playwright · Pytest · Pytest-BDD · Flask · Ruff

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install
```

Add a `.env` file (optional):

```
BASE_URL=https://www.saucedemo.com
BROWSER=chromium
HEADLESS=True
DEFAULT_TIMEOUT=5000
```

---

## Running Tests Directly

```powershell
pytest -v                                          # all tests
pytest tests/test_browser_launch.py -v            # single file
pytest -m smoke -v                                 # by marker
pytest -n auto -v                                  # parallel
pytest -k "Login with standard user" -v           # by name
```

---

## Running the Full Workflow (n8n + Flask)

### 1. Start n8n

```powershell
podman start n8n
```

Then open `http://localhost:5678` and import:
`n8n-workflows/QA Test Execution Orchestrator v3.json`

### 2. Start the Flask API

Open a **separate** PowerShell window:

```powershell
.venv\Scripts\Activate.ps1
python automation_services\test_runner.py
```

Leave this running. Flask listens on `http://localhost:5000`.

### 3. Trigger via n8n

Open `http://localhost:5678` and click **Execute workflow**.

n8n will POST to `/run-tests`, poll until the job completes, send the email, and attach the PDF — all automatically.

### 4. Verify manually (optional)

If you want to check the Flask API directly without n8n:

```powershell
# 1. Enqueue a run
$jobId = ((Invoke-WebRequest -Method POST http://localhost:5000/run-tests -UseBasicParsing).Content | ConvertFrom-Json).job_id
Write-Host "Job ID: $jobId"

# 2. Check status (run again after ~30 s to see 'completed')
(Invoke-WebRequest "http://localhost:5000/jobs/$jobId" -UseBasicParsing).Content | ConvertFrom-Json |
    Select-Object job_id, status, execution_status, summary

# 3. Download the PDF once completed
Invoke-WebRequest "http://localhost:5000/jobs/$jobId/download-report" -OutFile "QA_Report.pdf" -UseBasicParsing
```

---

## Flask API Reference

| Method | Endpoint                         | Description                                             |
| ------ | -------------------------------- | ------------------------------------------------------- |
| `POST` | `/run-tests`                     | Enqueue a test run → returns `202 {job_id}` immediately |
| `GET`  | `/jobs/<job_id>`                 | Poll status; includes full result when `completed`      |
| `GET`  | `/jobs`                          | Execution history, newest first                         |
| `GET`  | `/jobs/<job_id>/download-report` | Download per-job PDF                                    |
| `GET`  | `/download-report`               | Download latest completed job's PDF (n8n compat)        |

**Concurrency:** `max_workers=1` ensures only one pytest process runs at a time. Each job writes to its own `reports/jobs/<job_id>/` directory, so there are no shared files and no race conditions.

---

## Project Layout

```
components/      UI element wrappers (Button, TextInput, Label)
pages/           Page Objects
actions/         Business-level workflows
fixtures/        Pytest fixtures (browser, pages, data, screenshots)
tests/           Step definitions and test files
features/        Gherkin feature files
automation_services/  Flask API + PDF report generator
n8n-workflows/   n8n workflow JSON files
reports/jobs/    Per-run output (result.json, HTML, PDF)
```

---

## Code Quality

```powershell
ruff format .    # format
ruff check .     # lint
```

---

## Troubleshooting

- **ModuleNotFoundError** — ensure virtualenv is activated and imports use package-style paths.
- **Stale cache** — `Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force`
- **Playwright browser missing** — run `playwright install`
- **Port 5000 in use** — check for another Flask process: `netstat -ano | findstr :5000`
