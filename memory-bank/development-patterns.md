# Development Patterns

## Code Organization

### Repository Layout

```
project_root/
├── memory-bank/          # Project state & documentation (read-only for agents)
├── agent/                # PydanticAI agent logic
├── tools/                # Tool implementations (finance, research)
├── utils/                # Shared utilities (rate limiter, helpers)
├── app.py                # Streamlit entry point
├── config.py             # Configuration management
├── requirements.txt      # Dependency specifications
├── .env.example          # Environment variable template
├── .gitignore            # Git exclusions
├── git_tracker.md        # Commit history log
└── README.md             # Setup & usage documentation
```

### Module Boundaries

**Strict Separation:**
- **UI Layer (`app.py`):** Streamlit-specific code only. No direct API calls to YFinance/Tavily.
- **Agent Layer (`agent/core.py`):** PydanticAI agent setup, system prompts, tool registration. No UI logic.
- **Tool Layer (`tools/*.py`):** Isolated tool implementations. Each tool is self-contained with its own error handling.
- **Utilities (`utils/*.py`):** Reusable, framework-agnostic code (rate limiter, config loaders).

**Import Rules:**
- `app.py` may import from `agent/`, `config.py`
- `agent/core.py` may import from `tools/`, `utils/`, `config.py`
- `tools/*.py` may import from `utils/`, `config.py` (NOT from `agent/` or `app.py`)
- `utils/*.py` may import from `config.py` only

**Module Naming:**
- Avoid generic names that clash with library imports (e.g., no `telegram.py` if using `telegram` library)
- Use descriptive, specific names: `finance.py`, `research.py`, `rate_limiter.py`

### Path Management (Windows)

**Absolute Paths:**
- Use `pathlib.Path` for all file operations
- Convert to absolute paths when needed: `Path(__file__).resolve().parent`

**Module Resolution:**
- Add project root to `sys.path` at top of entry point if needed:
  ```python
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).resolve().parent))
  ```

## Coding Standards

### Naming Conventions

**Python Style (PEP 8):**
- **Modules/Packages:** `lowercase_with_underscores` (e.g., `rate_limiter.py`)
- **Classes:** `PascalCase` (e.g., `FinanceTool`, `RateLimiter`)
- **Functions/Variables:** `snake_case` (e.g., `get_stock_price`, `conversation_history`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_TICKER_LOOKUPS_PER_MINUTE`)
- **Private Members:** Prefix with single underscore `_internal_method`

**Descriptive Names:**
- Avoid abbreviations: `conversation_history` not `conv_hist`
- Exception: Common acronyms OK: `api_key`, `llm_model`

### Code Style

**Formatting:**
- **Line Length:** 88 characters (Black default)
- **Indentation:** 4 spaces (never tabs)
- **Quotes:** Double quotes `"` for strings (consistency with Black)
- **Imports:** Grouped and sorted (stdlib → third-party → local)
  ```python
  import sys
  from pathlib import Path

  import streamlit as st
  from pydantic_ai import Agent

  from agent.core import create_agent
  from config import settings
  ```

**Type Hints:**
- Mandatory for all function signatures:
  ```python
  def get_stock_price(ticker: str) -> dict[str, float | str]:
      ...
  ```
- Use `from __future__ import annotations` for forward references if needed

**Docstrings:**
- Google-style docstrings for all public functions/classes:
  ```python
  def fetch_stock_data(ticker: str) -> dict:
      """Fetches latest stock price for given ticker.

      Args:
          ticker: Stock ticker symbol (e.g., 'AAPL')

      Returns:
          Dictionary containing price, currency, and timestamp

      Raises:
          ValueError: If ticker is invalid or not found
          RateLimitError: If rate limit exceeded
      """
  ```

### Error Handling

**Philosophy: Fail Fast, Fail Loud**
- No silent failures or auto-retry logic
- Propagate errors to user with clear, actionable messages
- Include context in error messages for debugging

**Exception Patterns:**

**Custom Exceptions:**
```python
# utils/exceptions.py
class RateLimitExceededError(Exception):
    """Raised when ticker lookup rate limit is exceeded."""
    pass

class ToolExecutionError(Exception):
    """Raised when a tool fails to execute."""
    pass
```

**Tool Error Handling:**
```python
# tools/finance.py
def get_stock_price(ticker: str) -> dict:
    try:
        data = yfinance.Ticker(ticker).info
        if not data or 'regularMarketPrice' not in data:
            raise ValueError(f"Ticker '{ticker}' not found or data unavailable")
        return {"price": data['regularMarketPrice'], "currency": data.get('currency', 'USD')}
    except RateLimitExceededError:
        raise  # Propagate without wrapping
    except Exception as e:
        raise ToolExecutionError(f"YFinance API error for ticker '{ticker}': {str(e)}")
```

**UI Error Display:**
```python
# app.py
try:
    response = agent.run(user_input)
except RateLimitExceededError as e:
    st.error(f"Rate limit exceeded: {e}. Please wait before making more requests.")
except ToolExecutionError as e:
    st.error(f"Tool execution failed: {e}")
except Exception as e:
    st.error(f"Unexpected error: {e}")
    st.exception(e)  # Show full stack trace for debugging
```

**No Suppression:**
- Never use bare `except:` clauses
- Log exceptions before re-raising if needed
- Avoid generic `pass` in except blocks

## Testing Strategy

### Testing Pyramid Targets

**Unit Tests:** 70% of test suite
- All tool functions (`tools/finance.py`, `tools/research.py`)
- Utilities (`utils/rate_limiter.py`)
- Configuration loading (`config.py`)

**Integration Tests:** 25% of test suite
- Agent initialization with different model configs
- Agent + tool interaction (mocked external APIs)
- Streamlit session state management

**E2E Tests:** 5% of test suite
- Full user flow (model selection → query → streaming response)
- Use Playwright SKILL (NOT MCP) for browser automation

### Tools & Frameworks

**Unit Testing:**
- **Framework:** pytest (latest version)
- **Mocking:** unittest.mock for external API calls
- **Coverage Target:** Minimum 80% line coverage for non-UI code

**Integration Testing:**
- **Framework:** pytest with fixtures
- **Approach:** Mock external APIs (YFinance, Tavily, OpenAI, OLLAMA)
- **Fixtures:** Shared test data (sample stock responses, search results)

**E2E Testing:**
- **Framework:** Playwright (via Skill, NOT MCP)
- **Skill to Load:** `testing-patterns` skill for E2E setup guidance
- **Scope:** Critical user paths only (happy path + key error scenarios)

### Test Organization

```
tests/
├── unit/
│   ├── test_finance_tool.py
│   ├── test_research_tool.py
│   ├── test_rate_limiter.py
│   └── test_config.py
├── integration/
│   ├── test_agent_tools.py
│   └── test_session_state.py
├── e2e/
│   └── test_user_flow.py
├── fixtures/
│   └── sample_data.py
└── conftest.py              # Shared pytest configuration
```

### Test Naming

**Convention:** `test_<function>_<scenario>_<expected_result>`

Examples:
- `test_get_stock_price_valid_ticker_returns_price`
- `test_get_stock_price_invalid_ticker_raises_error`
- `test_rate_limiter_exceeds_limit_raises_exception`

### CI Gates (Future)

**Pre-Commit:**
- Linting: black, flake8, mypy
- Unit tests must pass
- Coverage threshold: 80%

**Pre-Merge:**
- All tests (unit + integration + E2E) must pass
- No type errors (mypy --strict)

## Security Practices

### Authentication & Authorization

**API Key Management:**
- All keys stored in `.env` file (NEVER in code)
- Load via `python-dotenv` at application startup
- Validate presence of required keys based on selected model:
  ```python
  # config.py
  import os
  from dotenv import load_dotenv

  load_dotenv()

  OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
  TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
  LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")

  def validate_config(model: str) -> None:
      if model == "openai" and not OPENAI_API_KEY:
          raise ValueError("OPENAI_API_KEY required for OpenAI model")
      if not TAVILY_API_KEY:
          raise ValueError("TAVILY_API_KEY required for research tool")
      if not LOGFIRE_TOKEN:
          raise ValueError("LOGFIRE_TOKEN required for observability")
  ```

**.env.example Template:**
```bash
# OpenAI API Configuration (required for OpenAI model)
OPENAI_API_KEY=sk-your-key-here

# Tavily API Configuration (required for research tool)
TAVILY_API_KEY=tvly-your-key-here

# LogFire Configuration (required for observability)
LOGFIRE_TOKEN=your-logfire-token-here

# OLLAMA Configuration (optional, defaults to localhost)
OLLAMA_BASE_URL=http://localhost:11434
```

### Input Hardening

**User Input Sanitization:**
- Trust Streamlit's built-in XSS protection for chat inputs
- No additional sanitization needed for PydanticAI (framework handles prompt isolation)

**Tool Input Validation:**
```python
# tools/finance.py
def validate_ticker(ticker: str) -> str:
    """Validates ticker symbol format."""
    ticker = ticker.strip().upper()
    if not ticker or len(ticker) > 10 or not ticker.isalpha():
        raise ValueError(f"Invalid ticker format: '{ticker}'")
    return ticker
```

**Rate Limiting as Security Control:**
- Prevents abuse of free YFinance API
- Implementation in `utils/rate_limiter.py`

### Secrets Protection

**Git Exclusions (.gitignore):**
```
# Environment variables
.env

# Python artifacts
__pycache__/
*.pyc
*.pyo
*.pyd

# Virtual environment
daniel/
venv/
env/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

**No Hardcoding:**
- Scan for accidental key commits before push
- Use placeholder values in documentation

## Tooling & Automation

### Linters & Formatters

**Code Formatting:**
- **Tool:** Black (opinionated formatter)
- **Config:** Default settings (88 char line length)
- **Usage:** `black .` before committing

**Linting:**
- **Tool:** Flake8 (style enforcement)
- **Ignored Rules:** E501 (line too long, handled by Black), W503 (line break before binary operator)
- **Usage:** `flake8 .`

**Type Checking:**
- **Tool:** mypy (static type checker)
- **Strictness:** Gradual adoption (start permissive, increase strictness)
- **Config:** `mypy.ini` with incremental mode
- **Usage:** `mypy .`

### Dependency Management

**requirements.txt:**
- Pin major versions, allow minor/patch updates:
  ```
  streamlit>=1.30.0,<2.0.0
  pydantic-ai>=0.0.14,<0.1.0
  ```
- Regenerate with `pip freeze > requirements.txt` after testing

**Virtual Environment:**
- Pre-existing `daniel` venv in project root
- Activation: `.\daniel\Scripts\activate` (Windows)
- Never commit venv to git

### Git Workflow

**Commit Discipline:**
- Commit after each logical feature completion
- Follow conventional commit format (optional but recommended):
  - `feat: Add YFinance integration tool`
  - `fix: Handle empty ticker responses gracefully`
  - `test: Add unit tests for rate limiter`

**git_tracker.md Maintenance:**
- Append one bullet per commit with timestamp and message:
  ```markdown
  - 2025-12-27 14:30 - feat: Initialize project structure and config
  - 2025-12-27 15:45 - feat: Implement rate limiter utility
  ```

**Branch Strategy:**
- Single main branch for this project scope
- Feature branches optional for experimental work

### Environment Activation

**Windows PowerShell/CMD:**
```cmd
.\daniel\Scripts\activate
```

**Verify Activation:**
```cmd
python --version  # Should show Python 3.14
pip list          # Should show installed packages in venv
```

### Running the Application

**Development Mode:**
```cmd
.\daniel\Scripts\activate
streamlit run app.py
```

**Testing:**
```cmd
.\daniel\Scripts\activate
pytest tests/ -v --cov=. --cov-report=term-missing
```

## Windows-Specific Considerations

### Encoding Safety

**No Emojis/Unicode in Code:**
- Avoid Unicode characters in print statements, comments, or docstrings
- Windows console may not support UTF-8 properly
- Use ASCII-safe alternatives:
  ```python
  # Good
  print("Rate limit exceeded. Please wait.")

  # Bad (may cause encoding errors on Windows)
  print("Rate limit exceeded ⚠️")
  ```

### Path Handling

**Use pathlib.Path:**
```python
from pathlib import Path

# Good (cross-platform)
config_path = Path(__file__).resolve().parent / "config" / "settings.json"

# Bad (Windows-specific)
config_path = "C:\\config\\settings.json"
```

### File Operations

**Explicit Encoding:**
```python
# Always specify encoding for file operations
with open("data.txt", "r", encoding="utf-8") as f:
    content = f.read()
```

## Code Review Checklist

Before marking any implementation complete:

- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] No hardcoded API keys or secrets
- [ ] Error messages are clear and actionable
- [ ] No silent exception handling (no bare `except` or `pass`)
- [ ] Tests written and passing for new code
- [ ] No Unicode/emojis in print statements or comments
- [ ] imports organized (stdlib → third-party → local)
- [ ] Code formatted with Black
- [ ] No module name clashes with library imports
- [ ] .env variables documented in .env.example
