class InventoryActions:
    def __init__(self, inventory_page):
        self.inventory_page = inventory_page

    def add_product_to_cart(self, product_name):
        return self.inventory_page.add_product_by_name(product_name)

    def remove_product_from_cart(self, product_name):
        return self.inventory_page.remove_product_by_name(product_name)

    def verify_cart_count(self, expected):
        actual = self.inventory_page.get_cart_count()
        assert actual == expected, f"Expected {expected} items, but got {actual}"

    def get_cart_count(self):
        return self.inventory_page.get_cart_count()

    def verify_inventory_loaded(self):
        return self.inventory_page.verify_inventory_loaded()

    def get_product_count(self):
        return self.inventory_page.get_product_count()
