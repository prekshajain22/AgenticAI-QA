import pytest


@pytest.mark.smoke
def test_open_swag_labs(page):
    page.goto("https://www.saucedemo.com/")

    assert page.title() == "Swag Labs"
