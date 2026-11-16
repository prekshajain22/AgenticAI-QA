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

pip install -e ".[dev]"
playwright install

cp .env.example .env             # then fill in the values you need — see below
```

Python dependencies are defined in `pyproject.toml`. The `dev` extra installs
Ruff for code quality checks; use `pip install -e .` for runtime dependencies
without Ruff. Run the service and test suite from the project checkout.

You don't need every value in `.env` filled in — only fill in what the
thing you're running actually uses (see the table below).

---

## Running the deterministic test suite

```bash
# Full suite (browser scenarios and framework unit tests)
pytest

# Application browser scenarios only
pytest tests/step_definitions

# Framework unit tests
pytest tests/unit

# Just smoke tests
pytest -m smoke

# Specific feature
pytest tests/features/login.feature

# Regression-marked tests only
pytest -m regression
```

### Checking components without LLM tokens

```bash
python -m pytest -o "addopts=" tests/unit -q
```

This runs the offline unit tests, including the Flask service's n8n-facing
endpoints, pipeline evidence validation, retry logic, and Jira comment publishing with
mocked external calls. It does not execute an n8n workflow or verify a live
MCP connection or Jira write. To check the live Jira + Playwright pipeline, run
`python -m agents.pipelines.jira_playwright` (it posts comments to Jira).

To test the application itself without an LLM, run
`pytest tests/step_definitions`. These browser scenarios access `BASE_URL` and
can create local reports and screenshots.

Cross-browser: set `BROWSER=chromium|firefox|webkit` in `.env`.
Headed mode for debugging: set `HEADLESS=False`.

Reports land in `output/reports/` (HTML), screenshots on failure in
`output/screenshots/`, logs in `output/logs/`.

---

## Running the AI agents

Each component can be run standalone for testing, or via its pipeline.

| Component                               | Type                                | Role                                                       |
| --------------------------------------- | ----------------------------------- | ---------------------------------------------------------- |
| `agents/jira/jira_bug_analyst_agent.py` | AI agent (AutoGen + Jira MCP)       | Fetches open bugs, produces a smoke test plan              |
| `agents/playwright/playwright_agent.py` | AI agent (AutoGen + Playwright MCP) | Executes the plan in a real browser, returns evidence      |
| `agents/pipelines/verification.py`      | Deterministic                       | Validates the structured evidence                          |
| `agents/jira/jira_comment_publisher.py` | Deterministic (no LLM)              | Posts validated results to Jira as comments                |
| `agents/analysis/ai_failure_agent.py`   | AI agent (AutoGen)                  | Explains a failed pytest test                              |
| `agents/analysis/report_analyzer.py`    | Deterministic orchestration         | Classifies failures and calls `AIFailureAgent` per failure |

Renamed modules (update any external scripts): `agents.jira.jira_bug_analyser` →
`agents.jira.jira_bug_analyst_agent`, `agents.jira.jira_reporter` →
`agents.jira.jira_comment_publisher`, and
`agents.analysis.report_analysis_agent.ReportAnalysisAgent` →
`agents.analysis.report_analyzer.ReportAnalyzer`. `agents/specs/jira_reporter.md` is a legacy
prompt spec that the current deterministic publisher does not use.

```bash
# Pipeline: Jira → Playwright → Jira (reads bugs, verifies them, reports back)
python -m agents.pipelines.jira_playwright

# Individual agents
python -m agents.jira.jira_bug_analyst_agent
python -m agents.playwright.playwright_agent
python -m agents.jira.jira_comment_publisher   # WARNING: posts a sample comment to Jira
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

`service/test_runner.py` exposes the application BDD browser scenarios and AI
failure analysis as an HTTP API for the n8n workflows in `n8n-workflows/`.
The `/run-tests` endpoint runs `tests/step_definitions`; framework unit tests
are run separately with `pytest tests/unit`.

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

| Endpoint                 | Method | Purpose                                                                               |
| ------------------------ | ------ | ------------------------------------------------------------------------------------- |
| `/run-tests`             | `POST` | Run application BDD browser scenarios, return results + AI analysis as JSON           |
| `/download-report`       | `GET`  | Download the PDF report from the most recent `/run-tests` run                         |
| `/run-jira-pipeline`     | `POST` | Start the Jira→Playwright→Jira pipeline in the background — returns `202` immediately |
| `/pipeline-status`       | `GET`  | Poll for the Jira pipeline's result                                                   |
| `/download-pipeline-pdf` | `GET`  | Download the PDF from the most recent Jira pipeline run                               |
| `/health`                | `GET`  | Liveness check                                                                        |

`/run-jira-pipeline` doesn't block — it kicks off the agent pipeline in the
background and returns immediately, since a 3-agent run with live browser
and Jira calls can take a while. Poll `/pipeline-status` until it reports
done, then hit `/download-pipeline-pdf`. This is what `QA Jira Pipeline
v2.json` does for you if you're driving it from n8n instead.

If `FLASK_SECRET` is set in `.env`, requests must include an
`X-Secret: <value>` header. It's unset by default for local use — set it
before exposing this service beyond your own machine.

The other workflows in `n8n-workflows/` follow the same start-Flask,
start-n8n, import-and-execute pattern — `QA Jira Pipeline v2.json` triggers
the `agents.pipelines.jira_playwright` agent pipeline instead of the pytest
suite; check its HTTP Request node for the exact endpoint it expects before
running it.

---

## Project layout

```
agents/        AI agent framework + Jira/Playwright agents + pipelines
automation/    Playwright Page Object Model — pages, components, actions, fixtures
service/       Flask API that runs the suite and serves reports
tests/         Feature files, step definitions, unit tests
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

## Generated files (safe to delete)

These are ignored by git and recreated on demand: `output/`, `reports/`, `screenshots/`,
`build/`, `*.egg-info/` (setuptools metadata created by `pip install -e .` or a build),
`.pytest_cache/`, `.ruff_cache/`, `.playwright-mcp/`, `__pycache__/`, and `*.log`.
Stop the Flask service before deleting `output/`, since `/download-report` serves from there.

## Code quality

```bash
ruff check .
ruff format .
```

CI (`.github/workflows/tests.yml`) runs linting and the full suite
(`pytest -v`) on every push and PR, and uploads the
HTML report and any failure screenshots as build artifacts.

---

## Troubleshooting

**`ModuleNotFoundError` for `mcp`, `httpx`, or `autogen_ext.tools.mcp`** —
run `pip install -e ".[dev]"` again. Dependency constraints are defined in
`pyproject.toml`, including AutoGen and MCP compatibility constraints.

**Jira agent hangs or errors with "command not found: uvx"** — install
[`uv`](https://docs.astral.sh/uv/); `mcp-atlassian` is launched through it.

**Playwright agent can't connect** — make sure Node.js is installed;
`@playwright/mcp` is launched via `npx`.

**"AI analysis unavailable" in a report** — no AI provider key is set, or
the configured model returned an empty response. Check `.env` and try a
different `*_MODEL` value.
