from automation.components.button import Button
from automation.components.text_input import TextInput
from automation.components.text_element import Label
from config.settings import BASE_URL
from automation.locators.login_locators import LoginLocators
from automation.pages.base_page import BasePage


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
        return self.inventory.is_visible()

    def verify_login_error(self):
        return self.error_banner.is_visible()
