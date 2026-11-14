from automation.components.button import Button
from automation.components.text_element import Label
from automation.components.text_input import TextInput
from automation.locators.login_locators import LoginLocators
from automation.pages.base_page import BasePage
from config.settings import BASE_URL


class LoginPage(BasePage):
    def __init__(self, page):
        super().__init__(page)

        self.username = TextInput(page, LoginLocators.USERNAME_INPUT, "Username")
        self.password = TextInput(page, LoginLocators.PASSWORD_INPUT, "Password")
        self.login_button = Button(page, LoginLocators.LOGIN_BUTTON, "Login Button")
        self.inventory = Label(page, LoginLocators.INVENTORY_CONTAINER, "Inventory List")
        self.error_banner = Label(page, LoginLocators.ERROR_BANNER, "Error Banner")

    def open_application(self):
        self.page.goto(BASE_URL)

    def login(self, username, password):
        self.username.enter(username)
        self.password.enter(password, sensitive=True)
        self.login_button.click()

    def verify_inventory_page(self):
        """Return True if inventory page is displayed after login.

        In CI/headless the navigation + rendering after clicking "Login" can be
        slower and "networkidle" is not always reliable. Prefer waiting for a
        stable UI element that definitively indicates the inventory page.
        """
        try:
            # SauceDemo inventory page container
            self.page.wait_for_selector(LoginLocators.INVENTORY_CONTAINER, timeout=15000)
            return self.inventory.is_visible()
        except Exception:
            return False

    def verify_login_error(self):
        return self.error_banner.is_visible()
