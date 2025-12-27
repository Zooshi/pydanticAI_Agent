# Additional Information & Strict Local Enforcement

## STRICT AGENT ENFORCEMENT

### Mandatory First Action on New Projects

  IF `memory-bank/` does NOT exist OR is empty:
    - IMMEDIATELY spawn **Product Manager Agent**
    - HALT all other actions
    - DO NOT read requirements yourself
    - DO NOT create any memory-bank files yourself

### Memory Bank File Ownership - NO EXCEPTIONS

- **Product Manager Agent ONLY** creates `projectbrief.md`
- **Technical Architect Agent ONLY** creates `technical-context.md` + `development-patterns.md` + `progress-tracker.md` (Initial Backlog)
- **Feature Implementer Agent** reads the backlog and *updates* `active-context.md` + `progress-tracker.md`
- **YOU CANNOT** create any memory-bank/*.md files directly; you must delegate.

### Pre-Implementation Checks (HALT if any fail)

  BEFORE writing any code, verify ALL exist:
    ✅ `memory-bank/projectbrief.md`
    ✅ `memory-bank/technical-context.md`
    ✅ `memory-bank/development-patterns.md`
    ✅ `memory-bank/progress-tracker.md` (Must contain ordered tasks)

  IF any missing → spawn appropriate agent, HALT.

### Task Classification (Objective Rules)

  Count these factors:

- Is `progress-tracker.md` empty? → **Architect Agent** (to create plan)
- Is there a backlog item ready? → **Feature Implementer Agent** (Iterative Loop)
- Is deployment requested? → **Security Auditor Agent**

  IF unclear → Spawn **Product Manager** to clarify scope.

### Self-Audit (Ask before every action)

  "Did a specialized agent create the architecture/plan I'm executing?"

- NO → Spawn agent NOW, do not proceed.
- YES → Continue.

## ENVIRONMENT & TECH STACK

- **OS**: Windows (Use backslashes `\` for paths where necessary).
- **Python**: Version 3.14.
- **Virtual Env**: A venv named "daniel" exists in the current folder.
  - *Activation*: `.\daniel\Scripts\activate` (Windows syntax).
- **Imports**: Add project root to `sys.path` at the top of scripts to fix module resolution if needed.
- **Naming**: strict avoidance of module name clashes (e.g., do NOT name a folder `telegram` if using the `telegram` library).

## PROCESS & TOOLS

### Git & History

- **Init**: Initialize an empty git repo at the start.
- **Ignore**: Always create `.gitignore` (include `.env`, `__pycache__`, `*.pyc`).
- **Tracker**: Maintain a `git_tracker.md` file. Add a bullet point for every commit with its message.
- **Milestones**: Commit regularly after every logical step (e.g., after each feature loop).

### Testing & Quality

- **Unit/Integration**: Mandatory for every feature.
- **E2E Testing**: Use **Playwright SKILL** (via progressive disclosure).
  - 🛑 **STRICT PROHIBITION**: Do NOT use the Playwright MCP.
- **Libraries**: Use **Context7 MCP** to fetch latest docs if libraries are unknown/new.

### Safety & Encoding

- **Encoding**: Do not use emojis/Unicode in print statements or code comments to avoid Windows encoding errors.
- **Secrets**: Create an `env.example` file. NEVER commit the actual `.env`.

## EXECUTION LOOP RECAP

1. **Architect** defines the backlog in `progress-tracker.md`.
2. **Orchestrator** (You) picks ONE task.
3. **Feature Implementer** builds it, updates tracker, and **TERMINATES**.
4. **Git**: Commit changes + update `git_tracker.md`.
5. *Repeat.*
