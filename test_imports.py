"""Verification script to test that all module imports work correctly.

This script tests:
- src package imports
- src.config imports
- src.agent package
- src.tools package
- src.utils package
"""

import sys
from pathlib import Path

# Add project root to sys.path for proper module resolution
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("Testing module imports...")
print("-" * 50)

# Test 1: Import src package
try:
    import src
    print("[OK] import src")
except ImportError as e:
    print(f"[FAIL] import src: {e}")
    sys.exit(1)

# Test 2: Import src.config module
try:
    from src import config
    print("[OK] from src import config")
except ImportError as e:
    print(f"[FAIL] from src import config: {e}")
    sys.exit(1)

# Test 3: Import specific items from src.config
try:
    from src.config import (
        ConfigurationError,
        validate_config,
        get_config_summary,
        OPENAI_API_KEY,
        TAVILY_API_KEY,
        LOGFIRE_TOKEN,
        OLLAMA_BASE_URL,
        OLLAMA_MODEL_NAME,
        MAX_TICKER_LOOKUPS_PER_MINUTE,
    )
    print("[OK] from src.config import ConfigurationError, validate_config, ...")
except ImportError as e:
    print(f"[FAIL] from src.config import ...: {e}")
    sys.exit(1)

# Test 4: Import src.agent package
try:
    from src import agent
    print("[OK] from src import agent")
except ImportError as e:
    print(f"[FAIL] from src import agent: {e}")
    sys.exit(1)

# Test 5: Import src.tools package
try:
    from src import tools
    print("[OK] from src import tools")
except ImportError as e:
    print(f"[FAIL] from src import tools: {e}")
    sys.exit(1)

# Test 6: Import src.utils package
try:
    from src import utils
    print("[OK] from src import utils")
except ImportError as e:
    print(f"[FAIL] from src import utils: {e}")
    sys.exit(1)

# Test 7: Verify config functions are callable
try:
    summary = get_config_summary()
    assert isinstance(summary, dict)
    print("[OK] get_config_summary() returns dict")
except Exception as e:
    print(f"[FAIL] get_config_summary() execution: {e}")
    sys.exit(1)

# Test 8: Verify ConfigurationError is an Exception
try:
    error = ConfigurationError("test")
    assert isinstance(error, Exception)
    print("[OK] ConfigurationError is an Exception")
except Exception as e:
    print(f"[FAIL] ConfigurationError instantiation: {e}")
    sys.exit(1)

print("-" * 50)
print("All import tests passed successfully!")
print()
print("Module structure verified:")
print("  - src/")
print("  - src/__init__.py")
print("  - src/config.py")
print("  - src/agent/__init__.py")
print("  - src/tools/__init__.py")
print("  - src/utils/__init__.py")
