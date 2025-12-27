# Technical Context

## Overview
- **Project Name:** PydanticAI Streamlit Financial Research Agent
- **One-line Summary:** Production-ready Streamlit app with PydanticAI agent for natural language financial research using YFinance and Tavily tools with dual-model support (OLLAMA local + OpenAI cloud).

## Technology Stack

### Core Framework & Language
**Language:** Python 3.14 (Windows environment)
**UI Framework:** Streamlit (latest stable version)
**Agent Framework:** PydanticAI (latest version with streaming support)

### LLM Providers
**Local Model:** OLLAMA with qwen3:8b model (pre-installed, assumed available)
**Cloud Model:** OpenAI gpt-4.1-mini (API key required)

### Data & Research APIs
**Financial Data:** YFinance (latest version, free, no authentication)
**Web Research:** Tavily API (requires TAVILY_API_KEY)

### Observability & Monitoring
**Tracking:** LogFire (requires LOGFIRE_TOKEN)

### Supporting Libraries
**Environment Management:** python-dotenv (for .env file loading)
**Rate Limiting:** Custom implementation using time-based sliding window
**HTTP Client:** requests (for Tavily API calls if needed beyond library wrapper)

## Architecture

### Style
**Monolithic Streamlit Application** - Single-process web app with embedded agent logic. Appropriate for the project scope with no multi-user persistence requirements.

### Context Diagram (textual)

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Browser                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend Layer                     │
│  - Chat UI with message history                                 │
│  - Model selection dropdown (OLLAMA/OpenAI)                     │
│  - Session state management (conversation history)              │
│  - Streaming response renderer                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Function Calls
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PydanticAI Agent Layer                       │
│  - Agent initialization with selected model                     │
│  - System prompt (ticker conversion instructions)               │
│  - Tool registration (finance_tool, research_tool)              │
│  - Streaming orchestration (chunk-based)                        │
│  - LogFire tracking integration                                 │
│  - Rate limiter wrapper (10 ticker lookups/min)                 │
└──────────┬─────────────────────────┬────────────────────────────┘
           │                         │
           │                         │
           ▼                         ▼
┌──────────────────────┐  ┌──────────────────────────┐
│   Finance Tool       │  │   Research Tool          │
│  (YFinance API)      │  │   (Tavily API)           │
│  - Ticker lookup     │  │  - Web search            │
│  - Latest price fetch│  │  - Result summarization  │
│  - Rate limit check  │  │  - API key auth          │
└──────────────────────┘  └──────────────────────────┘
           │                         │
           ▼                         ▼
    External APIs           External APIs
  (Yahoo Finance)         (Tavily Search)
```

### Component Responsibilities

**Streamlit UI Layer (`app.py`)**
- Render chat interface with alternating user/agent messages
- Manage model selection dropdown state
- Handle user input submission
- Stream agent responses chunk-by-chunk to UI
- Maintain session-based conversation history in `st.session_state`
- Display clear error messages on failures

**Agent Layer (`agent/core.py`)**
- Initialize PydanticAI agent with selected model configuration
- Define system prompt with ticker conversion instructions
- Register and manage tools (finance, research)
- Coordinate streaming response generation
- Integrate LogFire for conversation tracking
- Enforce transparency requirement (tool usage in responses)

**Tool Layer (`tools/finance.py`, `tools/research.py`)**
- `finance_tool`: YFinance integration for stock price lookups
- `research_tool`: Tavily API integration for web research
- Input validation and error handling per tool
- Rate limiting enforcement (finance tool only)

**Rate Limiter (`utils/rate_limiter.py`)**
- Sliding window implementation (10 requests per 60 seconds)
- Thread-safe for potential concurrent requests
- Clear error messages when limit exceeded

**Configuration (`config.py`)**
- Load environment variables from .env
- Validate required API keys based on selected model
- Expose configuration constants (rate limits, model names, etc.)

## Project Structure

```
C:\Users\danie\OneDrive\Desktop\cur\27122025\
├── memory-bank\
│   ├── projectbrief.md
│   ├── technical-context.md
│   ├── development-patterns.md
│   ├── progress-tracker.md
│   └── active-context.md
├── daniel\                      # Virtual environment (pre-existing)
├── agent\
│   ├── __init__.py
│   └── core.py                  # PydanticAI agent initialization & config
├── tools\
│   ├── __init__.py
│   ├── finance.py               # YFinance integration
│   └── research.py              # Tavily API integration
├── utils\
│   ├── __init__.py
│   └── rate_limiter.py          # Rate limiting logic
├── app.py                       # Streamlit main application
├── config.py                    # Environment & configuration management
├── requirements.txt             # Python dependencies
├── .env.example                 # Template for environment variables
├── .gitignore                   # Git ignore rules
├── git_tracker.md               # Commit history log
└── README.md                    # Setup and usage instructions
```

## Quality, SLOs & Performance

### Service Level Objectives (SLOs)
**Response Latency:**
- First chunk from agent: < 2 seconds (95th percentile)
- Tool execution (YFinance): < 1 second per ticker lookup (95th percentile)
- Tool execution (Tavily): < 3 seconds per search (95th percentile)

**Availability:**
- UI responsiveness: 99% uptime during active session
- Graceful degradation: Clear error messages on API failures (no silent failures)

**Rate Limiting:**
- Hard limit: 10 ticker lookups per minute (global, not per-user)
- Enforcement: Pre-tool execution check, clear error message on rejection

### Performance Considerations
- **Streaming:** Chunk-based delivery (not token-level) to balance UI smoothness with network efficiency
- **Session State:** In-memory conversation history - no disk I/O overhead
- **Caching:** No explicit caching layer (relies on API-level caching if available)
- **Model Selection Impact:** OLLAMA (local) expected faster for shorter responses; OpenAI (cloud) may have network latency but better reasoning

## Security & Compliance

### Threat Model

**High Priority Threats:**
1. **API Key Exposure** - OpenAI, Tavily, LogFire tokens in .env file
   - Mitigation: .gitignore enforcement, .env.example template, runtime validation
2. **Rate Limit Bypass** - Malicious user overwhelming YFinance API
   - Mitigation: Global rate limiter with sliding window, clear rejection messages
3. **Prompt Injection** - User input manipulating agent behavior
   - Mitigation: PydanticAI's built-in prompt isolation, no user input in system prompt

**Medium Priority Threats:**
4. **Denial of Service** - Expensive queries exhausting resources
   - Mitigation: Streamlit's single-session model limits blast radius, no auto-retry
5. **Data Leakage** - Sensitive queries logged to LogFire
   - Mitigation: Review LogFire data retention policies, assume queries are non-sensitive per use case

**Low Priority (Out of Scope):**
- Multi-user isolation (single-session app)
- SQL injection (no database)
- CSRF/XSS (Streamlit handles this)

### Security Controls

**Environment Variables:**
- All API keys stored in .env (never hardcoded)
- .env.example provided with placeholder values
- Runtime validation: Missing keys cause immediate failure with clear error

**Input Validation:**
- User chat input: Sanitized by PydanticAI and Streamlit
- Tool inputs: Validated within tool functions (e.g., ticker format checks)

**Error Handling:**
- No sensitive data in error messages (API keys redacted)
- Stack traces shown for debugging (acceptable for dev/demo, review for production)

**Dependencies:**
- Pin versions in requirements.txt to prevent supply chain attacks
- Regularly update dependencies for security patches

## Open Questions

1. **Python Version Discrepancy:** Project brief states Python 3.9, but environment context indicates Python 3.14. Confirm which version to target for compatibility testing.
   - **Assumption for now:** Python 3.14 (per latest environment context)

2. **OLLAMA Model Availability:** Assumed qwen3:8b is pre-installed and accessible via OLLAMA on localhost. Confirm OLLAMA API endpoint (default: http://localhost:11434).

3. **LogFire Integration Depth:** Confirm whether to track:
   - Only agent responses (lightweight)
   - Full conversation history (moderate)
   - Tool execution details + latencies (comprehensive)
   - **Assumption for now:** Full conversation history + tool usage transparency

4. **Chunk Size for Streaming:** PydanticAI streaming behavior depends on model. Confirm if chunk size control is needed or rely on framework defaults.
   - **Assumption for now:** Use PydanticAI default chunk behavior

5. **Rate Limiter Scope:** Confirm rate limit applies to:
   - Only YFinance ticker lookups (per brief: "ticker lookups")
   - All tool calls (YFinance + Tavily)
   - **Assumption for now:** Only YFinance ticker lookups (10/min)

## Dependencies & Versions

*To be finalized in requirements.txt during implementation phase.*

**Core:**
- streamlit>=1.30.0
- pydantic-ai>=0.0.14
- python-dotenv>=1.0.0

**APIs:**
- yfinance>=0.2.40 (latest as of Jan 2025)
- tavily-python>=0.3.0 (or requests for manual API calls)
- openai>=1.10.0 (for OpenAI model support)
- ollama>=0.1.0 (Python client for OLLAMA API)

**Observability:**
- logfire>=0.20.0

**Utilities:**
- requests>=2.31.0 (for Tavily if needed)
