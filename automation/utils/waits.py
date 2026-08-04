from playwright.sync_api import Locator, Page

from config.settings import DEFAULT_TIMEOUT


class Waits:
    DEFAULT_TIMEOUT = DEFAULT_TIMEOUT

    @staticmethod
    def until_visible(locator: Locator, timeout=DEFAULT_TIMEOUT):
        locator.wait_for(
            state="visible",
            timeout=timeout,
        )

    @staticmethod
    def until_hidden(locator: Locator, timeout=DEFAULT_TIMEOUT):
        locator.wait_for(
            state="hidden",
            timeout=timeout,
        )

    @staticmethod
    def until_attached(locator: Locator, timeout=DEFAULT_TIMEOUT):
        locator.wait_for(state="attached", timeout=timeout)

    @staticmethod
    def until_detached(locator: Locator, timeout=DEFAULT_TIMEOUT):
        locator.wait_for(
            state="detached",
            timeout=timeout,
        )

    @staticmethod
    def until_url(page: Page, url, timeout=DEFAULT_TIMEOUT):
        page.wait_for_url(
            url,
            timeout=timeout,
        )

    @staticmethod
    def until_load(page: Page):
        page.wait_for_load_state("load")

    @staticmethod
    def until_network_idle(page: Page):
        page.wait_for_load_state("networkidle")
