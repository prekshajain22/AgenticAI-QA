from automation.components.base_component import BaseComponent


class Checkbox(BaseComponent):
    def check(self):

        self.wait_until_visible()
        self.logger.info(f"Checking '{self.name}'")
        self.locator.check()

    def uncheck(self):
        self.wait_until_visible()
        self.logger.info(f"Unchecking '{self.name}'")
        self.locator.uncheck()

    def is_checked(self):
        self.wait_until_visible()
        self.logger.info(f"Checking status of '{self.name}'")
        return self.locator.is_checked()
