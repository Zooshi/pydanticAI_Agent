---
name: memory-bank-templates
description: Templates for all memory bank files (projectbrief.md, technical-context.md, development-patterns.md, active-context.md, progress-tracker.md). Load this skill when creating or updating memory bank documentation.
---

This skill provides templates for memory bank files that maintain project state across sessions. Use these templates when initializing or updating the memory-bank directory.

## projectbrief.md Template

```markdown
# [Project Name]

## Problem Statement
[2-3 sentences describing the core problem this project solves]

## Solution Approach  
[2-3 sentences describing how this project solves the problem]

## Target Users
[1-2 sentences describing who will use this and how]

## Success Criteria
- [Specific, measurable outcome 1]
- [Specific, measurable outcome 2]  
- [Specific, measurable outcome 3]

## Project Scope

**In Scope:**
- [Feature/capability 1]
- [Feature/capability 2]

**Out of Scope:**
- [Explicitly excluded feature 1]
- [Explicitly excluded feature 2]

## Key Constraints
- [Technical constraint 1]
- [Business constraint 1]
- [Timeline constraint 1]
```

## technical-context.md Template

```markdown
# Technical Context

## Technology Stack
**Language:** [Primary language + version]
**Framework:** [Framework + version]
**Database:** [Database + version]
**Infrastructure:** [Deployment target/platform]
**Key Dependencies:** [List critical dependencies]

## Architecture Overview
**Style:** [Monolith/Microservices/Serverless/etc]
**Data Flow:** [High-level data flow description]
**External Integrations:** [APIs, services, databases]

## Key Technical Decisions
1. **[Decision 1]:** [Rationale and implications]
2. **[Decision 2]:** [Rationale and implications]

## Development Environment

**Setup Commands:**
```bash
[Commands to set up local development environment]
```

**Build & Test:**
```bash
[Commands to build and test the project]
```

**Deployment:**
```bash
[Commands to deploy the project]
```

## Performance Requirements
- [Specific performance requirement 1]
- [Specific performance requirement 2]

## Security Considerations
- [Security requirement 1]
- [Security requirement 2]
```

## development-patterns.md Template

```markdown
# Development Patterns

## Code Style & Conventions
**File Naming:** [Convention used]
**Function Naming:** [Convention used]
**Variable Naming:** [Convention used]

## Error Handling Pattern
[Specific pattern used - Result types, exceptions, etc.]

## Testing Strategy
**Unit Tests:** [Coverage target and approach]
**Integration Tests:** [Approach and tools]
**E2E Tests:** [When and how they're run]

## Logging & Monitoring
**Log Level:** [Default log level]
**Log Format:** [Structured logging format]
**Monitoring:** [What metrics are tracked]

## Code Organization
**Directory Structure:** [How code is organized]
**Module Boundaries:** [How functionality is divided]
```

## active-context.md Template

```markdown
# Active Context

## Current Focus
[What is actively being worked on right now]

## Recent Changes
- [Change 1 with date]
- [Change 2 with date]
- [Change 3 with date]

## Next Steps
1. [Immediate next action]
2. [Following action]
3. [Future consideration]

## Open Questions
- [Question needing resolution]

## Blockers
- [Any blocking issues]
```

## progress-tracker.md Template

```markdown
# Progress Tracker

## Completed Features
- [x] [Feature 1] - [completion date]
- [x] [Feature 2] - [completion date]

## In Progress
- [ ] [Feature 3] - [status/blocker]

## Planned
- [ ] [Feature 4]
- [ ] [Feature 5]

## Known Issues
| Issue | Severity | Status |
|-------|----------|--------|
| [Issue 1] | High/Medium/Low | Open/In Progress |

## Technical Debt
- [Debt item 1] - [impact/priority]
- [Debt item 2] - [impact/priority]
```

## Memory Bank Update Protocol

**Agent Responsibilities:**
- Product Manager: projectbrief.md
- Technical Architect: technical-context.md, development-patterns.md
- Project Implementer: progress-tracker.md, active-context.md  
- Security Auditor: technical-context.md (security sections)

**Conflict Resolution:**
When inconsistencies detected: Stop → Analyze → Ask user → Update systematically → Verify
