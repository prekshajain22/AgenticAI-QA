Feature: Login

    @smoke
    Scenario: Login with standard user
        Given I Open The Application
        When I Login Using User "standard_user"
        Then I Should See The Inventory Page

    @regression
    Scenario: Login with invalid credentials should fail and capture screenshot
        Given I Open The Application
        When I Login Using User "invalid_user"
        Then I Should See A Login Error
