# PydanticAI Streamlit Financial Research Agent

## Problem Statement
Users need an interactive, transparent AI assistant that can provide real-time financial data and web research capabilities without requiring technical knowledge of stock tickers or API integrations. Current solutions lack transparency in tool usage, require manual ticker lookups, and don't offer flexible model selection between local and cloud-based LLMs.

## Solution Approach
Build a production-ready Streamlit web application powered by PydanticAI framework that enables users to interact with an intelligent agent through natural language. The agent automatically converts company names to stock tickers, fetches financial data via YFinance, performs web research using Tavily, and streams responses with full transparency about which tools are being used. Users can choose between a local OLLAMA model (qwen3:8b) or OpenAI's gpt-4.1-mini, with all interactions tracked via LogFire for observability.

## Target Users
- Financial analysts and investors who need quick access to stock prices and market research
- Business professionals researching companies without technical knowledge of stock ticker symbols
- Developers and data scientists who want a transparent, observable AI agent for financial workflows
- Teams requiring flexible deployment options (local models for privacy, cloud models for performance)

## Success Criteria
- Fully functional, production-ready application deployable on any hosting stack
- Agent successfully converts company names to stock tickers without hardcoded mappings (instruction-based AI conversion)
- Streaming responses display in real-time with chunk-based delivery
- Tool usage is explicitly mentioned in agent responses for full transparency
- Model selection (OLLAMA vs OpenAI) works seamlessly via dropdown interface
- All user interactions are tracked and observable through LogFire integration
- Error messages are clear and detailed for development/debugging purposes
- Rate limiting prevents API abuse (max 10 ticker lookups per minute)
- Session-based conversation history persists during active session only

## Project Scope

**In Scope:**
- Streamlit frontend with chat interface (alternating user/agent messages)
- Model selection dropdown (OLLAMA qwen3:8b local or OpenAI gpt-4.1-mini)
- PydanticAI agent framework integration with two tools:
  - Finance tool: YFinance API for latest stock prices (free, no API key)
  - Research tool: Tavily API for web research (requires API key)
- Intelligent company name to stock ticker conversion (AI-driven, no hardcoding)
- Agent capability to use both tools sequentially in a single response
- Chunk-based streaming responses with real-time display
- Explicit tool usage transparency in agent responses
- Session-based conversation history (no cross-session persistence)
- LogFire integration for conversation tracking and observability
- Rate limiting: Maximum 10 ticker lookups per minute
- Environment variable configuration with .env.example file
- Clear, detailed error messages for debugging (no auto-retry, no fallback)
- Production-ready code structure and error handling

**Out of Scope:**
- Conversation history persistence across sessions or to database
- User authentication or multi-user support
- Custom financial analysis or portfolio management features
- Automatic model fallback on errors
- Auto-retry mechanisms for failed API calls
- Historical stock data analysis or charting
- Real-time stock price alerts or notifications
- Mobile application or responsive mobile optimization
- OLLAMA model installation or configuration (assumed pre-installed)
- Custom LogFire dashboard creation
- Advanced rate limiting per user (single global rate limit only)

## Key Constraints
- **Environment**: Windows OS, Python 3.9, OLLAMA already installed with qwen3:8b model available
- **Framework**: Must use PydanticAI framework for agent implementation
- **UI Framework**: Must use Streamlit for frontend interface
- **API Dependencies**:
  - YFinance (latest version, free, no authentication)
  - Tavily API (requires API key)
  - OpenAI API (requires API key for gpt-4.1-mini)
  - LogFire (requires project token)
- **Rate Limiting**: Hard limit of 10 ticker lookups per minute to prevent YFinance API abuse
- **Error Handling Philosophy**: Display detailed errors for debugging; no silent failures, no automatic fallbacks
- **Ticker Conversion**: Must be AI instruction-based, absolutely no hardcoded company name to ticker mappings
- **Session Management**: History exists only during active session, cleared on new session start
- **Streaming**: Must use chunk-based streaming (not token-by-token) compatible with PydanticAI and Streamlit

## Open Questions
- None (all requirements clarified with user)
