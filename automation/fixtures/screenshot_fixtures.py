import os

import pytest

from config.settings import TEST_RUNNER_OUTPUT_DIR, TEST_RUNNER_SCREENSHOTS_DIR

SCREENSHOT_DIR = f"{TEST_RUNNER_OUTPUT_DIR}/{TEST_RUNNER_SCREENSHOTS_DIR}"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):

    outcome = yield
    report = outcome.get_result()

    setattr(item, "rep_" + report.when, report)

    if report.when != "call" or not report.failed:
        return

    report.failure_message = str(report.longrepr)

    page = item.funcargs.get("page")
    if page is None:
        return  # Not a browser test (e.g. a unit test) - nothing to capture

    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        screenshot_path = f"{SCREENSHOT_DIR}/{item.name}.png"
        page.screenshot(path=screenshot_path, full_page=True)
        item.screenshot_path = screenshot_path
    except Exception as exc:  # noqa: BLE001 - never mask the real test failure
        print(f"Could not capture failure screenshot: {exc}")
