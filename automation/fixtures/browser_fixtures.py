import pytest
from playwright.sync_api import Playwright

from config.settings import DEFAULT_NAVIGATION_TIMEOUT, DEFAULT_TIMEOUT, HEADLESS, SLOW_MO


@pytest.fixture(scope="function")
def page(playwright: Playwright):

    browser = playwright.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)

    context = browser.new_context()
    page = context.new_page()

    page.set_default_timeout(DEFAULT_TIMEOUT)  # 5 seconds
    page.set_default_navigation_timeout(DEFAULT_NAVIGATION_TIMEOUT)  # 10 seconds

    yield page

    context.close()
    browser.close()
