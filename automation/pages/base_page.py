from automation.utils.logger import get_logger
from automation.utils.waits import Waits
from config.settings import DEFAULT_TIMEOUT


class BasePage:
    def __init__(self, page):
        self.page = page
        self.logger = get_logger()

    def open_url(self, url):
        self.logger.info(f"Opening URL: {url}")
        self.page.goto(url)
        Waits.until_load(self.page)

    def click(self, locator):
        self.page.locator(locator).wait_for(state="visible")
        self.page.locator(locator).click()

    def enter_text(self, locator, text):
        self.page.locator(locator).wait_for(state="visible")
        self.page.locator(locator).fill(text)

    def wait_for_visible(self, locator, timeout=DEFAULT_TIMEOUT):
        self.page.locator(locator).wait_for(state="visible", timeout=timeout)

    def screenshot(self, name):
        self.page.screenshot(path=f"screenshots/{name}.png")
