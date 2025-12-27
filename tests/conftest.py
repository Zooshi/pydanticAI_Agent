"""Shared pytest configuration and fixtures for all tests.

This module provides common test fixtures and pytest configuration
used across unit, integration, and E2E tests.
"""

import sys
from pathlib import Path

import pytest


# Add project root to sys.path for module imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables between tests to prevent interference.

    This fixture runs automatically for every test and ensures clean state.
    """
    import os
    original_env = os.environ.copy()
    yield
    # Restore original environment after test
    os.environ.clear()
    os.environ.update(original_env)
