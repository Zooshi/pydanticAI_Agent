---
name: code-patterns
description: Result-type patterns, error handling, naming conventions, and architecture standards for Python and TypeScript. Load this skill when implementing business logic, data processing, or establishing code quality patterns.
---

This skill provides code patterns for consistent, maintainable implementations. Use these patterns for all business logic, error handling, and data processing.

## Result-Type Pattern

All operations should return structured Result types for predictable error handling.

### Python Implementation

```python
from typing import Optional, TypeVar, Generic
from dataclasses import dataclass, field
import logging

T = TypeVar('T')

@dataclass
class Result(Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

def process_data(raw_data: dict) -> Result[dict]:
    """Process data with comprehensive error handling."""
    try:
        logging.info(f"Processing data for {raw_data.get('id', 'unknown')}")
        
        if not raw_data or not isinstance(raw_data, dict):
            return Result(success=False, error="Invalid input data format")
        
        processed = validate_and_transform(raw_data)
        
        return Result(
            success=True, 
            data=processed,
            metadata={"processed_at": datetime.now().isoformat()}
        )
    except ValidationError as e:
        logging.error(f"Validation failed: {e}")
        return Result(success=False, error=f"Validation error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return Result(success=False, error="Internal processing error")
```

### TypeScript Implementation

```typescript
interface Result<T> {
  success: boolean;
  data?: T;
  error?: string;
  metadata?: Record<string, unknown>;
}

interface ProcessingOptions {
  strictMode: boolean;
  timeoutMs: number;
  retryAttempts: number;
}

export const processData = async <T>(
  rawData: Record<string, unknown>,
  options: Partial<ProcessingOptions> = {}
): Promise<Result<T>> => {
  const config: ProcessingOptions = {
    strictMode: true,
    timeoutMs: 5000,
    retryAttempts: 3,
    ...options
  };

  try {
    if (!rawData || typeof rawData !== 'object') {
      return { success: false, error: 'Invalid input data format' };
    }

    const processed = await withTimeout(
      processWithRetry(rawData, config),
      config.timeoutMs
    );
    
    return {
      success: true,
      data: processed,
      metadata: { processedAt: new Date().toISOString() }
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return {
      success: false,
      error: config.strictMode ? errorMessage : 'Processing failed'
    };
  }
};
```

## Error Handling Standards

- **Structured Error Types**: UserError (4xx), SystemError (5xx), ServiceError (external)
- **Never Silent Failures**: Always return Result or raise explicitly
- **Sanitized Logging**: No sensitive data in logs (passwords, tokens, PII)
- **Graceful Degradation**: User-friendly messages, fallback behavior
- **Retry Logic**: Exponential backoff for external services

## Naming Conventions

| Type | Convention | Examples |
|------|------------|----------|
| Functions | verb_noun / verbNoun | `process_payment`, `validateUser` |
| Variables | descriptive nouns | `user_email`, `paymentResult` |
| Constants | UPPER_SNAKE_CASE | `API_BASE_URL`, `MAX_RETRIES` |
| Booleans | is/has/can prefix | `isValid`, `hasPermission` |
| Files | snake_case or kebab-case | `user_service.py`, `payment-processor.ts` |
| Classes | PascalCase | `UserService`, `PaymentProcessor` |

## Architecture Standards

- **Dependency Injection**: For external services and testability
- **Interface Segregation**: Small, focused interfaces
- **Resource Cleanup**: Context managers, try/finally
- **Configuration**: Environment variables, validated on startup

## Performance Patterns

- **Data Structures**: Choose optimal (HashMap vs Array, Set vs List)
- **Complexity**: Consider O(n) implications
- **Caching**: Redis, in-memory, CDN where appropriate
- **Async I/O**: async/await for network operations
- **Database**: Indexes, avoid N+1, connection pooling
- **Batching**: Bulk operations when possible
- **Pagination**: For large datasets
- **Lazy Loading**: For expensive operations
