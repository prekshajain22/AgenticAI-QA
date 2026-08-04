import os

import pytest


@pytest.fixture(autouse=True)
def capture_screenshot_on_failure(request):
    """Capture a screenshot on test failure.

    Uses request.getfixturevalue('page') lazily so this fixture is safe
    for unit tests that have no Playwright page — it simply skips the
    screenshot rather than forcing a browser launch.
    """
    yield

    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        try:
            page = request.getfixturevalue("page")
        except pytest.FixtureLookupError:
            return  # No Playwright page available (unit test) — skip screenshot

        screenshot_dir = "output/screenshots"

        os.makedirs(screenshot_dir, exist_ok=True)

        screenshot_path = f"{screenshot_dir}/{request.node.name}.png"

        page.screenshot(
            path=screenshot_path,
            full_page=True,
        )

        request.node.screenshot_path = screenshot_path


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):

    outcome = yield

    report = outcome.get_result()

    setattr(item, "rep_" + report.when, report)

    if report.when == "call":
        if report.failed:
            report.failure_message = str(report.longrepr)
