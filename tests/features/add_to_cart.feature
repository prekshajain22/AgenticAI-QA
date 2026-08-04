Feature: Add to cart functionality

    @smoke
    Scenario: Add product to cart and verify cart badge
        Given I Open The Application
        When I Login Using User "standard_user"
        And I Add "Sauce Labs Backpack" To Cart
        Then I Should See Cart Count As "1"

    @regression
    Scenario: Add multiple products to cart
        Given I Open The Application
        When I Login Using User "standard_user"
        And I Add "Sauce Labs Backpack" To Cart
        And I Add "Sauce Labs Bike Light" To Cart
        Then I Should See Cart Count As "2"
