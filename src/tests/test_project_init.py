# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Smoke tests confirming project scaffolding."""

import adsl


def test_package_version() -> None:
    assert adsl.__version__ == "0.1.0"