from pytest_bdd import given, parsers, then, when


@given("I Open The Application")
def open_application(login_page):
    login_page.open_application()


@when(parsers.parse('I Login Using User "{user_type}"'))
def login(login_actions, user_type):
    login_actions.login_as(user_type)


@then("I Should See The Inventory Page")
def verify_inventory_page(login_page):
    assert login_page.verify_inventory_page(), "Inventory page was not displayed after login."


@then("I Should See A Login Error")
def verify_login_error(login_page):
    assert login_page.verify_login_error(), "Login error banner was not displayed for invalid credentials."
