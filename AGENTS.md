# Agentic QA Framework — How the Agents Work

## The big picture

This framework contains **two independent AI-powered pipelines**, each made
of one or more agents that communicate by passing plain text from one to the
next. Both pipelines are built from the same two core classes:

| Class          | File                      | Role                                                                                      |
| -------------- | ------------------------- | ----------------------------------------------------------------------------------------- |
| `AgentFactory` | `agents/agent_factory.py` | Creates any `AssistantAgent` — inject a model client once, build agents from prompts      |
| `MCPConfig`    | `agents/mcp_config.py`    | Central config — returns a Gemini model client, Jira MCP params, or Playwright MCP params |

---

## Pipeline 1 — Jira → Playwright smoke test

```
┌─────────────────────────────────────────────────────────┐
│  agents/pipelines/jira_playwright.py                    │
│                                                         │
│  Stage 1                        Stage 2                 │
│  ┌─────────────────┐  smoke test ┌────────────────────┐ │
│  │ JiraBugAnalyser │ ──────────► │  PlaywrightAgent   │ │
│  │  (Jira MCP)     │  plan text  │  (Playwright MCP)  │ │
│  └─────────────────┘             └────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Stage 1 — JiraBugAnalyser (`agents/jira/jira_bug_analyser.py`)

- **Tools**: Jira MCP (`uvx mcp-atlassian`) — real Jira read access
- **Prompt**: `agents/prompts/jira_bug_analyst.py`
- **What it does**: Fetches the 5 most recent bugs from Jira, identifies patterns,
  designs a step-by-step smoke test scenario for the application.
- **Handoff signal**: Ends its response with `HANDOFF TO AUTOMATION`.

### Stage 2 — PlaywrightAgent (`agents/playwright/playwright_agent.py`)

- **Tools**: Playwright MCP (`npx @playwright/mcp@latest`) — controls a real browser
- **Prompt**: `agents/prompts/playwright_automation.py`
- **Input**: The smoke test plan text produced by JiraBugAnalyser.
- **What it does**: Executes every step in the browser, takes screenshots at
  checkpoints, reports PASS / FAIL per step.
- **Completion signal**: Ends with `TESTING COMPLETE`.

### Credentials

Read from `test_data/users.json` — no hardcoded passwords anywhere.

### Run it

```bash
# Full pipeline: Jira bugs → Playwright browser verification
python -m agents.pipelines.jira_playwright

# Bug analysis only (no browser)
python -m agents.jira.jira_bug_analyser

# Playwright standalone demo (no Jira needed)
python -m agents.playwright.playwright_agent
```

---

## Pipeline 2 — Test run → AI failure analysis

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  pytest run  ──►  output/reports/result.json                 │
│                           │                                  │
│              ┌────────────▼──────────────┐                   │
│              │  ReportAnalysisAgent      │                   │
│              │  (reads JSON, extracts    │                   │
│              │   each failed test)       │                   │
│              └────────────┬──────────────┘                   │
│                           │  per-failure dict                │
│              ┌────────────▼──────────────┐                   │
│              │  AIFailureAgent           │                   │
│              │  (OpenAI — classifies,    │                   │
│              │   root-causes, fixes)     │                   │
│              └────────────┬──────────────┘                   │
│                           │                                  │
│              output/reports/ai_analysis.json                 │
└──────────────────────────────────────────────────────────────┘
```

### ReportAnalysisAgent (`agents/analysis/report_analysis_agent.py`)

- **Not** an AutoGen agent — it is a plain Python class that reads a pytest
  JSON report and orchestrates the analysis.
- Calls `AIFailureAgent.analyse()` for every failed test.

### AIFailureAgent (`agents/analysis/ai_failure_agent.py`)

- **Model**: OpenAI (configurable via `OPENAI_MODEL` env var)
- **What it does**: Given a test name, error message, and logs, returns a
  structured analysis: failure classification, root cause, recommended fix,
  confidence score.
- **Design note**: Intentionally synchronous (wraps `asyncio.run()`) so it
  can be called from pytest hooks and Flask routes without async plumbing.

### Run it

```bash
# Via the Flask service (runs tests + generates analysis automatically)
python service/test_runner.py

# Or directly against an existing result.json
python agents/analysis/report_analysis_agent.py
```

---

## Agents directory layout

```
agents/
  __init__.py                        ← public API: AgentFactory, MCPConfig
  agent_factory.py                   ← AgentFactory class
  mcp_config.py                      ← MCPConfig class
  jira/
    __init__.py
    jira_bug_analyser.py             ← Jira bug fetcher agent
  playwright/
    __init__.py
    playwright_agent.py              ← Playwright browser executor agent
  pipelines/
    __init__.py
    jira_playwright.py               ← Pipeline 1 orchestrator
  analysis/
    __init__.py
    ai_failure_agent.py              ← AI failure analyser (OpenAI, sync)
    report_analysis_agent.py         ← Report reader + orchestrator
  prompts/
    __init__.py
    jira_bug_analyst.py              ← JiraBugAnalyser system message template
    playwright_automation.py         ← PlaywrightAgent system message template
```

---

## Model providers (free options)

| Provider | Env var          | Free limit | Notes                                                        |
| -------- | ---------------- | ---------- | ------------------------------------------------------------ |
| Gemini   | `GEMINI_API_KEY` | 1M TPM     | `gemini-1.5-flash` — use aistudio.google.com key (`AIza...`) |
| OpenAI   | `OPENAI_API_KEY` | Paid       | `OPENAI_MODEL` — used only by AIFailureAgent                 |

`MCPConfig.default_client()`

> **Gemini model rules**: use bare names (`gemini-1.5-flash`, `gemini-2.0-flash`).
> Never use `models/` prefix or `*-lite`/`*-latest` variants — they break tool calling.

---

## How to extend

### Add a new agent

1. Add a prompt template in `agents/prompts/my_prompt.py` with a `build(**kwargs) -> str` function.
2. If a new MCP server is needed, add a `@staticmethod` to `MCPConfig`.
3. Create the agent with the factory:
   ```python
   factory = AgentFactory(model_client=MCPConfig.default_client())
   agent = factory.create_agent(
       name="MyNewAgent",
       system_message=my_prompt.build(...),
       workbench=my_mcp,
   )
   ```
4. Add a unit test in `tests/unit/`.

### Swap the model

## Replace `MCPConfig.default_client()` with `MCPConfig.gemini_client()` or

## Environment variables required

| Variable         | Used by                                         |
| ---------------- | ----------------------------------------------- |
| `GEMINI_API_KEY` | All Gemini-powered agents (Pipeline 1 fallback) |
| `GEMINI_MODEL`   | Gemini model name (default: `gemini-1.5-flash`) |
| `JIRA_URL`       | JiraBugAnalyser (Jira MCP)                      |
| `JIRA_USERNAME`  | JiraBugAnalyser (Jira MCP)                      |
| `JIRA_API_TOKEN` | JiraBugAnalyser (Jira MCP)                      |
| `OPENAI_API_KEY` | AIFailureAgent (Pipeline 2)                     |
| `OPENAI_MODEL`   | AIFailureAgent model name                       |
| `BASE_URL`       | PlaywrightAgent (app under test)                |
