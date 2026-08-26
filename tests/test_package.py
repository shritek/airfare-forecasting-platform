"""Smoke tests for the installable package boundary."""

from importlib.metadata import version

import airfare_forecasting


def test_package_is_installed() -> None:
    """The development environment installs the project and its metadata."""
    assert airfare_forecasting.__name__ == "airfare_forecasting"
    assert version("airfare-forecasting-platform") == "0.1.0"
