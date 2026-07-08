"""Smoke tests confirming project scaffolding."""

import adsl


def test_package_version() -> None:
    assert adsl.__version__ == "0.1.0"