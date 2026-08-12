import pytest

from config.settings import BASE_URL


@pytest.mark.smoke
@pytest.mark.integration
def test_open_swag_labs(page):
    page.goto(BASE_URL)

    assert page.title() == "Swag Labs"
