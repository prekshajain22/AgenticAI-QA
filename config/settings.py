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
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "CRED")
JIRA_PROJECT_NAME = os.getenv("JIRA_PROJECT_NAME", "CreditBank")
