from components.button import Button
from components.text_element import Label
from locators.inventory_locators import InventoryLocators
from pages.base_page import BasePage


class InventoryPage(BasePage):
    def __init__(self, page):
        super().__init__(page)

        self.inventory_container = Label(
            page,
            InventoryLocators.INVENTORY_CONTAINER,
            "Inventory Container",
        )
        self.cart_badge = Label(page, InventoryLocators.CART_BADGE, "Cart Badge")
        self.cart_link = Button(page, InventoryLocators.CART_LINK, "Cart Link")
        self.sort_dropdown = Label(page, InventoryLocators.SORT_CONTAINER, "Sort Dropdown")

    def verify_inventory_loaded(self):
        """Verify that inventory page is loaded"""
        self.logger.info("Verifying inventory page is loaded")
        return self.inventory_container.is_visible()

    def get_product_count(self):
        """Get total number of products displayed"""
        self.logger.info("Getting product count")
        products = self.page.locator(InventoryLocators.PRODUCT_ITEM).count()
        self.logger.info(f"Found {products} products")
        return products

    def add_product_by_index(self, index):
        """Add product to cart by index"""
        self.logger.info(f"Adding product at index {index} to cart")
        products = self.page.locator(InventoryLocators.PRODUCT_ITEM).nth(index)
        add_button = products.locator(InventoryLocators.ADD_TO_CART_BUTTON)
        add_button.click()
        self.logger.info(f"Product at index {index} added to cart")

    def add_product_by_name(self, product_name):
        """Add product to cart by product name"""
        self.logger.info(f"Adding product '{product_name}' to cart")
        products = self.page.locator(InventoryLocators.PRODUCT_ITEM)
        count = products.count()

        for i in range(count):
            name_element = products.nth(i).locator(InventoryLocators.PRODUCT_NAME)
            if name_element.text_content().strip() == product_name:
                add_button = products.nth(i).locator(InventoryLocators.ADD_TO_CART_BUTTON)
                add_button.click()
                self.logger.info(f"Product '{product_name}' added to cart")
                return True

        self.logger.warning(f"Product '{product_name}' not found")
        return False

    def remove_product_by_name(self, product_name):
        """Remove product from cart by product name"""
        self.logger.info(f"Removing product '{product_name}' from cart")
        products = self.page.locator(InventoryLocators.PRODUCT_ITEM)
        count = products.count()

        for i in range(count):
            name_element = products.nth(i).locator(InventoryLocators.PRODUCT_NAME)
            if name_element.text_content().strip() == product_name:
                remove_button = products.nth(i).locator(InventoryLocators.REMOVE_BUTTON)
                if remove_button.is_visible():
                    remove_button.click()
                    self.logger.info(f"Product '{product_name}' removed from cart")
                    return True

        self.logger.warning(f"Product '{product_name}' not found or already removed")
        return False

    def get_cart_count(self):
        """Get the current cart item count from badge"""
        self.logger.info("Getting cart count")
        if self.cart_badge.is_visible():
            count = int(self.cart_badge.locator.text_content())
            self.logger.info(f"Cart count: {count}")
            return count
        self.logger.info("Cart is empty (no badge visible)")
        return 0

    def go_to_cart(self):
        """Navigate to cart page"""
        self.logger.info("Navigating to cart")
        self.cart_link.click()

    def get_product_price(self, product_name):
        """Get price of a specific product"""
        self.logger.info(f"Getting price for product '{product_name}'")
        products = self.page.locator(InventoryLocators.PRODUCT_ITEM)
        count = products.count()

        for i in range(count):
            name_element = products.nth(i).locator(InventoryLocators.PRODUCT_NAME)
            if name_element.text_content().strip() == product_name:
                price_element = products.nth(i).locator(InventoryLocators.PRODUCT_PRICE)
                price = price_element.text_content()
                self.logger.info(f"Price for '{product_name}': {price}")
                return price

        self.logger.warning(f"Product '{product_name}' not found")
        return None
