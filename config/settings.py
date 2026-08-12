import os

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://www.saucedemo.com")
BROWSER = os.getenv("BROWSER", "chromium").lower()
HEADLESS = os.getenv("HEADLESS", "True").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "0"))

if not BASE_URL:
    raise ValueError("BASE_URL is not set. Check environment config.")

DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", 5000))
DEFAULT_NAVIGATION_TIMEOUT = int(os.getenv("DEFAULT_NAVIGATION_TIMEOUT", 10000))
FRAMEWORK = os.getenv("FRAMEWORK", "Playwright")
ENVIRONMENT = os.getenv("ENVIRONMENT", "QA")

# AI model keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# AI model names (with sensible defaults)
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")

# Jira
JIRA_URL = os.getenv("JIRA_URL")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")
JIRA_PROJECT_NAME = os.getenv("JIRA_PROJECT_NAME")

# Flask test runner
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))

TEST_RUNNER_OUTPUT_DIR = os.getenv("TEST_RUNNER_OUTPUT_DIR", "output")
TEST_RUNNER_REPORTS_DIR = os.getenv("TEST_RUNNER_REPORTS_DIR", "reports")
TEST_RUNNER_LOGS_DIR = os.getenv("TEST_RUNNER_LOGS_DIR", "logs")
TEST_RUNNER_SCREENSHOTS_DIR = os.getenv("TEST_RUNNER_SCREENSHOTS_DIR", "screenshots")

TEST_RUNNER_QA_REPORT_FILENAME = os.getenv(
    "TEST_RUNNER_QA_REPORT_FILENAME", "QA_Execution_Report.pdf"
)
TEST_RUNNER_JIRA_PIPELINE_REPORT_FILENAME = os.getenv(
    "TEST_RUNNER_JIRA_PIPELINE_REPORT_FILENAME", "Jira_Pipeline_Report.pdf"
)

TEST_RUNNER_RUN_TESTS_ENDPOINT = os.getenv("TEST_RUNNER_RUN_TESTS_ENDPOINT", "/run-tests")
TEST_RUNNER_RUN_JIRA_PIPELINE_ENDPOINT = os.getenv(
    "TEST_RUNNER_RUN_JIRA_PIPELINE_ENDPOINT", "/run-jira-pipeline"
)
TEST_RUNNER_PIPELINE_STATUS_ENDPOINT = os.getenv(
    "TEST_RUNNER_PIPELINE_STATUS_ENDPOINT", "/pipeline-status"
)
TEST_RUNNER_HEALTH_ENDPOINT = os.getenv("TEST_RUNNER_HEALTH_ENDPOINT", "/health")
TEST_RUNNER_DOWNLOAD_REPORT_ENDPOINT = os.getenv(
    "TEST_RUNNER_DOWNLOAD_REPORT_ENDPOINT", "/download-report"
)
TEST_RUNNER_DOWNLOAD_PIPELINE_PDF_ENDPOINT = os.getenv(
    "TEST_RUNNER_DOWNLOAD_PIPELINE_PDF_ENDPOINT", "/download-pipeline-pdf"
)
