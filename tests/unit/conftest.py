"""Unit-test fixtures.

pytest-playwright's session-scoped sync fixture keeps an event loop running in
the main thread. When browser tests run first in the same session, any later
test that calls ``asyncio.run`` fails with "cannot be called from a running
event loop". Run the coroutine in a worker thread in that case.
"""

import asyncio
import concurrent.futures

import pytest


@pytest.fixture(autouse=True)
def _asyncio_run_works_after_browser_tests(monkeypatch):
    real_run = asyncio.run

    def run(coro, **kwargs):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return real_run(coro, **kwargs)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(real_run, coro, **kwargs).result()

    monkeypatch.setattr(asyncio, "run", run)
