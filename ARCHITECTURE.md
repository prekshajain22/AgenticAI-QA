# Architecture

This is the single source of truth for _how_ AgenticAI-QA is built and _why_.
For setup and day-to-day commands, see [README.md](README.md).

---

## System overview

AgenticAI-QA is two systems sharing one repo:

1. **A deterministic automation layer** — Playwright + pytest-BDD, Page Object
   Model, run either directly or via a Flask service that n8n orchestrates.
   This layer is CI-friendly: same input, same output, every time.
2. **An agentic AI layer** — a small reusable agent framework (`agents/`)
   built on AutoGen and MCP, with two pipelines running on top of it. This
   layer is non-deterministic by nature — it calls an LLM — and is designed
   around that fact rather than pretending it isn't true.

Keeping these separate matters: the deterministic suite is what you'd trust
for a real regression gate; the agent layer is what makes the system able to
read a Jira ticket, act on it, and report back without a human in the loop.
Neither one pretends to be the other.

---

## Package map

```
agenticai-qa/
├── agents/                        AI agent framework
│   ├── agent_factory.py           AgentFactory — builds AssistantAgent from a prompt + model client
│   ├── mcp_config.py              MCPConfig — model clients (Gemini/OpenRouter/OpenAI) + MCP server params
│   ├── jira/
│   │   ├── jira_bug_analyser.py   Stage 1 — fetches Jira bugs, designs a smoke test plan
│   │   └── jira_reporter.py       Stage 3 — posts verified results back to Jira as comments
│   ├── playwright/
│   │   └── playwright_agent.py    Stage 2 — executes a smoke test plan in a real browser via MCP
│   ├── pipelines/
│   │   ├── jira_playwright.py     Orchestrates stages 1 → 2 → 3, gated by the verification layer
│   │   ├── evidence_schema.py     Canonical schema for Stage 2 → 3 structured evidence records
│   │   └── verification.py        Deterministic validation of evidence before Stage 3 runs
│   ├── analysis/
│   │   ├── ai_failure_agent.py        Classifies a pytest failure, suggests a fix (sync wrapper)
│   │   └── report_analysis_agent.py   Reads a pytest JSON report, calls AIFailureAgent per failure
│   └── prompts/                   System-message templates — one `build(**kwargs)` per agent
│       ├── jira_bug_analyst.py
│       ├── jira_reporter.py
│       ├── playwright_automation.py
│       └── failure_analysis.py
│
├── automation/                    Browser-automation framework (Page Object Model)
│   ├── actions/                   Business workflows — LoginActions, InventoryActions
│   ├── components/                UI wrappers — Button, Label, TextInput, Checkbox, Dropdown
│   ├── fixtures/                  Pytest fixtures — browser, pages, actions, data, screenshots
│   ├── locators/                  CSS / data-test selectors
│   ├── pages/                     Page Objects — BasePage, LoginPage, InventoryPage
│   └── utils/                     logger, waits, data_reader, assertions
│
├── service/                       Flask test-runner API
│   ├── test_runner.py             POST /run-tests → pytest → AI analysis → PDF → JSON
│   └── pdf_report_generator.py    ReportLab PDF builder
│
├── tests/
│   ├── features/                  Gherkin .feature files
│   ├── step_definitions/          pytest-BDD step implementations
│   ├── unit/                      Fast, offline tests — no browser, no network, no LLM calls
│   └── integration/                Live tests — real Jira, real LLM, real browser; excluded from CI
│
├── config/settings.py             All env-var config, in one place, with fail-fast validation
├── test_data/users.json           Credential fixtures (SauceDemo users)
├── scripts/check_mcp_connection.py  Manual Jira MCP connectivity check (not a test)
├── n8n-workflows/                 Exported n8n workflow JSON
└── output/                        Generated artefacts, gitignored
    ├── reports/<run_id>/          result.json · test_report.html · QA_Execution_Report.pdf
    ├── logs/flask.log
    └── screenshots/
```

---

## The agent framework

Two classes are the entire foundation every agent is built from:

| Class          | File                      | Responsibility                                                                                                            |
| -------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `AgentFactory` | `agents/agent_factory.py` | Takes a model client once; builds any number of `AssistantAgent`s from a name, a prompt, and optionally a tool/workbench. |
| `MCPConfig`    | `agents/mcp_config.py`    | Static factory for model clients (Gemini, OpenRouter, OpenAI) and MCP server connection params (Jira, Playwright).        |

Everything else is composition on top of these two:

- **Prompts** (`agents/prompts/`) are plain functions — `build(**kwargs) -> str` —
  kept separate from agent logic so a prompt can be read, diffed, and tuned
  without touching orchestration code.
- **Agents** (`agents/jira/`, `agents/playwright/`, `agents/analysis/`) each
  wire one prompt + one model client + (optionally) one MCP workbench into an
  `AssistantAgent`, and expose a plain `async def run(...) -> str` function.
- **Pipelines** (`agents/pipelines/`) chain agents together, passing one
  agent's text output as the next agent's task input.

**Why this shape:** adding a new agent should never mean re-learning AutoGen
boilerplate. It means: write a prompt, decide which model/MCP server it
needs (already covered by `MCPConfig` or a one-method addition to it), and
call `factory.create_agent(...)`. The framework code doesn't grow when the
agent count grows.

**Provider abstraction:** every agent gets its model client from
`MCPConfig.default_client()`, which tries providers in order
(OpenRouter → Gemini) and raises a clear error if none are configured.
Individual agents can also request a specific provider
(`AIFailureAgent` always uses OpenAI, since it's judged worth the cost for
report quality). Swapping providers for the rest is a `.env` change, not a
code change.

---

## Pipeline 1 — Jira → Playwright → Jira

The end-to-end agentic workflow: verify whether bugs reported in Jira still
reproduce, using a real browser, and write the verified result back.

```
JiraBugAnalyser (Jira MCP: uvx mcp-atlassian)
  reads the most recent open bugs, finds patterns, writes a smoke test plan
  → ends with: HANDOFF TO AUTOMATION

PlaywrightAgent (Playwright MCP: npx @playwright/mcp)
  executes the smoke test plan step by step in a real browser
  → ends with: TESTING COMPLETE

JiraReporter (Jira MCP)
  finds the issue keys referenced in the execution report, posts a
  PASS / FAIL / INCONCLUSIVE comment on each
  → ends with: JIRA UPDATED
```

Stage transitions 1→2 and 2→3 use a sentinel string at the end of each
agent's output (`HANDOFF TO AUTOMATION`, `TESTING COMPLETE`,
`JIRA UPDATED`) as a lightweight readiness signal — good enough for a
linear pipeline; it isn't the thing standing between the agents and Jira.

**Run it:** `python -m agents.pipelines.jira_playwright`

### Verification layer (Stage 2 → Stage 3)

This is the part that stops a hallucinated result from becoming a real
Jira comment. `PlaywrightAgent` doesn't just narrate PASS/FAIL in prose —
its prompt requires a machine-readable JSON array (schema defined once, in
`agents/pipelines/evidence_schema.py`) between two literal markers,
`STRUCTURED_EVIDENCE_START` / `STRUCTURED_EVIDENCE_END`, one record per
step: `{step, status, issue_key, expected, actual, screenshot_path,
evidence_type}`.

Before `JiraReporter` ever runs, `agents/pipelines/verification.py` does
this, entirely in plain Python — no LLM involved:

- extracts and parses the JSON block (missing/malformed → immediate
  `INCONCLUSIVE`, pipeline doesn't proceed on trust)
- rejects any record missing a required field or using a status outside
  `PASS` / `FAIL` / `INCONCLUSIVE`
- **checks the claimed screenshot file actually exists on disk** — a
  step can't claim evidence that isn't there
- rejects self-contradictory records (e.g. `status: PASS` while `actual`
  says the check failed)

Only records that pass all of this — `validated_records` — are handed to
`JiraReporter`, along with the list of `verification_errors`. The
reporter's prompt is explicit: use only the validated JSON, never infer an
outcome from Stage 1/2 prose, and write `INCONCLUSIVE` rather than guess
when a given issue has no validated record. That instruction is
prompt-enforced, not code-enforced — the _evidence_ an issue's comment can
be based on is guaranteed correct by `verification.py`; the exact wording
JiraReporter writes from that evidence is still model output. That's the
honest boundary of what's currently deterministic in this pipeline versus
what's still LLM-judgment, and it's a meaningfully smaller trust surface
than before.

---

## Pipeline 2 — Test run → AI failure analysis

The simpler pipeline: turn a pytest failure into a usable diagnosis,
automatically, as part of every test run.

```
pytest run → output/reports/<run_id>/result.json
  → ReportAnalysisAgent reads the JSON, extracts each failed test
  → AIFailureAgent (OpenAI) classifies it, root-causes it, suggests a fix
  → merged into the JSON/PDF report served by service/test_runner.py
```

`ReportAnalysisAgent` is plain Python, not an AutoGen agent — it owns the
heuristic classification (assertion vs. timeout vs. locator error) and only
calls out to `AIFailureAgent` for the natural-language root-cause narrative.
Keeping the heuristic layer separate means the report still has _some_
structured, non-LLM-dependent signal even if the AI call fails or is
disabled entirely — which `AIFailureAgent` degrades to gracefully
(`"AI analysis unavailable: ..."`) rather than breaking the run.

`AIFailureAgent` is intentionally synchronous — the rest of the call chain
(pytest hooks, Flask routes) is sync, and it wasn't worth making the whole
stack async for one feature. It bridges into AutoGen's async API via
`asyncio.run()`, with a thread-pool fallback for the case where an event
loop is already running.

**Run it:** starts automatically as part of `python service/test_runner.py`
→ `POST /run-tests`.

---

## Configuration

Everything is read once, in `config/settings.py`, from environment
variables (loaded via `.env`, see `.env.example` for the full list with
comments). A few values fail fast with a clear error at import time
(`BASE_URL`) rather than surfacing a confusing failure deep inside a test
run; most AI/Jira keys are validated lazily, at the point they're first
needed, so the deterministic test suite works with zero AI configuration.

| Variable                                        | Default                     | Used by                                                |
| ----------------------------------------------- | --------------------------- | ------------------------------------------------------ |
| `BASE_URL`                                      | `https://www.saucedemo.com` | `automation/`, PlaywrightAgent                         |
| `BROWSER`                                       | `chromium`                  | `browser_fixtures`                                     |
| `HEADLESS`                                      | `True`                      | `browser_fixtures`                                     |
| `FLASK_SECRET`                                  | _(empty — auth disabled)_   | `service/test_runner.py`                               |
| `OPENROUTER_API_KEY` / `OPENROUTER_MODEL`       | —                           | `MCPConfig.default_client()` (tried first)             |
| `GEMINI_API_KEY` / `GEMINI_MODEL`               | —                           | `MCPConfig.default_client()` (fallback)                |
| `OPENAI_API_KEY` / `OPENAI_MODEL`               | —                           | `AIFailureAgent` only                                  |
| `JIRA_URL` / `JIRA_USERNAME` / `JIRA_API_TOKEN` | —                           | JiraBugAnalyser, JiraReporter                          |
| `JIRA_PROJECT_KEY` / `JIRA_PROJECT_NAME`        | _(required, no default)_    | Pipeline 1 — `.env.example` uses `SAUCE` / `SauceDemo` |

`service/test_runner.py` exposes both pipelines over HTTP; endpoint paths
are themselves configurable (`TEST_RUNNER_*_ENDPOINT` in `.env.example`,
shown here at their defaults):

| Endpoint                 | Method | Purpose                                                       |
| ------------------------ | ------ | ------------------------------------------------------------- |
| `/run-tests`             | `POST` | Run the pytest suite, return results + AI failure analysis    |
| `/download-report`       | `GET`  | Download the PDF from the most recent `/run-tests` run        |
| `/run-jira-pipeline`     | `POST` | Start Pipeline 1 in the background, returns `202` immediately |
| `/pipeline-status`       | `GET`  | Poll for the Jira pipeline's result                           |
| `/download-pipeline-pdf` | `GET`  | Download the PDF from the most recent Jira pipeline run       |
| `/health`                | `GET`  | Liveness check                                                |

`/run-jira-pipeline` is async (submit → poll) rather than blocking, unlike
`/run-tests` — sensible, since a 3-agent pipeline with live browser and
Jira calls can run considerably longer than a pytest suite, and holding an
HTTP connection open for that isn't a great pattern (n8n's HTTP node has
a timeout either way).

---

## Design decisions worth knowing the "why" for

**Why AutoGen, not raw LLM API calls?** Multi-agent coordination with tool
use is exactly what AgentChat is built for — rebuilding a tool-call loop and
message history by hand would duplicate what the framework already does
well, for no real benefit here.

**Why MCP instead of a hand-rolled Jira/Playwright client?** MCP servers
(`mcp-atlassian`, `@playwright/mcp`) are maintained integrations. Using them
means the agent gets real Jira and browser tools without this repo owning
that integration surface — and it's the direction tool-calling is
standardizing on generally.

**Why is the agent layer separate from the deterministic Playwright suite,
rather than one framework?** They have different reliability guarantees.
The `automation/` layer is meant to be a trustworthy CI gate — same result
every run. The agent layer calls an LLM and is inherently non-deterministic.
Merging them would either make the deterministic suite flaky, or make the
agent layer pretend to be more reliable than it is. Keeping them separate,
with the agent layer explicitly labeled as such, is more honest about what
each part actually guarantees.

**Why text-sentinel handoffs for stage readiness, but a real schema for
evidence?** Different jobs. The sentinel strings only signal "this stage
is done, the next one can start" — plain text is fine for that. But the
data the next stage _acts on_ (whether a bug reproduced, what proves it)
needed to be structured and validated, which is why that boundary
specifically (Stage 2 → 3) got a real schema (`evidence_schema.py`) and a
deterministic validator (`verification.py`) instead of more prose. Apply
the same test to any future stage: is this just "go ahead," or is it a
claim something downstream will act on? The former can stay a sentinel;
the latter should be a schema.

---

## How to extend

**Add a new agent:**

1. Write a prompt template in `agents/prompts/my_prompt.py` with a
   `build(**kwargs) -> str` function.
2. If it needs a new MCP server or model provider, add a `@staticmethod`
   to `MCPConfig`.
3. Build it with the factory:
   ```python
   factory = AgentFactory(model_client=MCPConfig.default_client())
   agent = factory.create_agent(
       name="MyNewAgent",
       system_message=my_prompt.build(...),
       workbench=my_mcp,
   )
   ```
4. Add a unit test in `tests/unit/` (mock `agent.run`, don't hit a real API)
   and, if it talks to a real external service, an integration test in
   `tests/integration/` marked `@pytest.mark.integration`.

**Add a new pipeline stage:** follow the existing sentinel-string handoff
pattern only if the pipeline stays linear. If you're adding branching logic
(retry a stage, conditionally skip one), that's the signal to move to a
structured return type instead of prose — don't extend the sentinel-string
pattern past a simple linear chain.

**Swap the default model provider:** change `MCPConfig.default_client()`'s
provider order, or call a specific `MCPConfig.<provider>_client()` directly
from an agent that needs a specific provider regardless of what else is
configured (see `AIFailureAgent`, which always uses OpenAI).
