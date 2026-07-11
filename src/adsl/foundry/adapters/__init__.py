# Copyright (c) 2026 Apostolos Kalogritsas
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license information.

"""Foundry storage adapters."""

from adsl.foundry.adapters.local import LocalDatasetAdapter
from adsl.foundry.adapters.http import HttpDatasetAdapter

__all__ = ["LocalDatasetAdapter", "HttpDatasetAdapter"]