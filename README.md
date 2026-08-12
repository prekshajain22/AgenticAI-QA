# AgenticAI-QA

A QA automation framework combining a Playwright/pytest-BDD test suite with
an AI agent layer (AutoGen + MCP) that reads Jira bugs, verifies them in a
real browser, and reports back automatically.

For how it's built and why, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Quick start

```bash
git clone https://github.com/prekshajain22/AgenticAI-QA.git
cd AgenticAI-QA

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
playwright install

cp .env.example .env             # then fill in the values you need — see below
```

You don't need every value in `.env` filled in — only fill in what the
thing you're running actually uses (see the table below).

---

## Running the deterministic test suite

```bash
# Full suite
pytest

# Just smoke tests
pytest -m smoke

# Specific feature
pytest tests/features/login.feature

# Skip anything that hits a real external service (Jira, LLMs, live browser)
pytest -m "not integration"
```

Cross-browser: set `BROWSER=chromium|firefox|webkit` in `.env`.
Headed mode for debugging: set `HEADLESS=False`.

Reports land in `output/reports/` (HTML), screenshots on failure in
`output/screenshots/`, logs in `output/logs/`.

---

## Running the AI agents

Each agent can be run standalone for testing, or via its pipeline.

```bash
# Pipeline: Jira → Playwright → Jira (reads bugs, verifies them, reports back)
python -m agents.pipelines.jira_playwright

# Individual agents
python -m agents.jira.jira_bug_analyser
python -m agents.playwright.playwright_agent
python -m agents.jira.jira_reporter
```

Requires, at minimum, one AI provider key (`OPENROUTER_API_KEY` or
`GEMINI_API_KEY`) and, for the Jira agents, `JIRA_URL` / `JIRA_USERNAME` /
`JIRA_API_TOKEN`. See [ARCHITECTURE.md](ARCHITECTURE.md#configuration) for
the full variable list and what each agent actually needs.

The Jira agents connect via `mcp-atlassian`, launched through `uvx` — you'll
need [`uv`](https://docs.astral.sh/uv/) installed on your machine
(`pip install uv` or see their install docs) for these to work. The
Playwright agent connects via `npx @playwright/mcp`, which needs Node.js
installed.

To sanity-check your Jira MCP connection before running a full agent:

```bash
python scripts/check_mcp_connection.py
```

---

## Running the full pipeline as a service (n8n)

`service/test_runner.py` exposes the pytest suite + AI failure analysis as
an HTTP API, so it can be triggered and monitored externally — the intended
use is via the n8n workflows in `n8n-workflows/`.

### 1. Activate the environment

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Start the Flask service

```powershell
python service\test_runner.py
```

Binds to `0.0.0.0:5001` by default (override with `FLASK_PORT` in `.env`).
Leave this running — it's the API n8n calls. Check it's up:

```powershell
Invoke-WebRequest http://localhost:5001/health -UseBasicParsing
```

### 3. Start n8n

```powershell
podman start n8n
```

Open **http://localhost:5678** and import
`n8n-workflows/QA Test Execution Orchestrator v3.json` if it isn't already
there.

### 4. Trigger it

Click **Execute workflow** in the n8n UI — it POSTs to `/run-tests`, waits
for the full run to finish, then emails the PDF report.

- **Set the n8n HTTP Request node's timeout to at least 600s (10 min).**
  `/run-tests` blocks until pytest, PDF generation, and AI analysis are all
  complete — a short timeout will kill the connection before Flask responds.
- n8n reaches Flask via `http://host.containers.internal:5001` — this
  resolves the host machine from inside the podman container. If n8n can't
  connect, confirm Flask is running and bound to `0.0.0.0` (the default).

### 5. Verify without n8n

```powershell
$result = (Invoke-WebRequest -Method POST http://localhost:5001/run-tests -UseBasicParsing).Content | ConvertFrom-Json
$result | Select-Object run_id, execution_status, summary

Invoke-WebRequest http://localhost:5001/download-report -OutFile QA_Report.pdf -UseBasicParsing
```

Useful for confirming the Flask/pytest/AI side works before troubleshooting
n8n specifically.

### Flask API reference

| Endpoint           | Method | Purpose                                             |
| ------------------ | ------ | --------------------------------------------------- |
| `/run-tests`       | `POST` | Run the suite, return results + AI analysis as JSON |
| `/download-report` | `GET`  | Download the PDF report from the most recent run    |
| `/health`          | `GET`  | Liveness check                                      |

If `FLASK_SECRET` is set in `.env`, requests must include an
`X-Secret: <value>` header. It's unset by default for local use — set it
before exposing this service beyond your own machine.

The other workflows in `n8n-workflows/` follow the same start-Flask,
start-n8n, import-and-execute pattern — `QA Jira Pipeline v1.json` triggers
the `agents.pipelines.jira_playwright` agent pipeline instead of the pytest
suite; check its HTTP Request node for the exact endpoint it expects before
running it.

---

## Project layout

```
agents/        AI agent framework + Jira/Playwright agents + pipelines
automation/    Playwright Page Object Model — pages, components, actions, fixtures
service/       Flask API that runs the suite and serves reports
tests/         Feature files, step definitions, unit tests, integration tests
config/        All environment-variable configuration, in one place
n8n-workflows/ Exported n8n orchestration workflows
```

Full package-by-package breakdown: [ARCHITECTURE.md](ARCHITECTURE.md#package-map).

---

## Environment variables

Copy `.env.example` to `.env` and fill in what you need — nothing here is
required just to run the deterministic test suite against SauceDemo.

| Variable                                                          | Needed for                                     |
| ----------------------------------------------------------------- | ---------------------------------------------- |
| `BASE_URL`, `BROWSER`, `HEADLESS`, timeouts                       | Test suite (sensible defaults already set)     |
| `OPENROUTER_API_KEY` / `GEMINI_API_KEY` / `OPENAI_API_KEY`        | Any AI agent — pick at least one free provider |
| `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY` | Jira agents / pipeline                         |
| `FLASK_SECRET`                                                    | The Flask service, if exposed beyond localhost |

Generate a Flask secret with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Code quality

```bash
ruff check .
ruff format .
```

CI (`.github/workflows/tests.yml`) runs linting and the full suite
(`pytest -v -m "not integration"`) on every push and PR, and uploads the
HTML report and any failure screenshots as build artifacts.

---

## Troubleshooting

**`ModuleNotFoundError` for `mcp`, `httpx`, or `autogen_ext.tools.mcp`** —
run `pip install -r requirements.txt` again; these are pinned there
specifically because AutoGen's MCP extras have tight version requirements.

**Jira agent hangs or errors with "command not found: uvx"** — install
[`uv`](https://docs.astral.sh/uv/); `mcp-atlassian` is launched through it.

**Playwright agent can't connect** — make sure Node.js is installed;
`@playwright/mcp` is launched via `npx`.

**"AI analysis unavailable" in a report** — no AI provider key is set, or
the configured model returned an empty response. Check `.env` and try a
different `*_MODEL` value.
