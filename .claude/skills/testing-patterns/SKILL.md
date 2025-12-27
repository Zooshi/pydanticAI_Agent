---
name: testing-patterns
description: Test patterns and examples for Python (pytest) and TypeScript (Vitest), including unit tests, integration tests, E2E testing with Playwright, and coverage targets. Load this skill when writing tests or setting up test infrastructure.
---

This skill provides testing patterns and examples for comprehensive test coverage. Use these patterns when writing tests or establishing testing infrastructure.

## Python Testing (pytest)

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from your_module import process_data, Result

class TestProcessData:
    """Comprehensive test suite for data processing."""
    
    def test_successful_processing(self):
        """Test successful data processing with valid input."""
        input_data = {"id": "123", "email": "test@example.com"}
        result = process_data(input_data)
        
        assert result.success is True
        assert result.data is not None
        assert result.error is None
        assert "processed_at" in result.metadata
    
    def test_invalid_input_handling(self):
        """Test handling of invalid input data."""
        result = process_data(None)
        assert result.success is False
        assert "Invalid input" in result.error
    
    def test_validation_error_handling(self):
        """Test handling of validation errors."""
        with patch('your_module.validate_and_transform') as mock:
            mock.side_effect = ValidationError("Invalid email")
            result = process_data({"email": "invalid"})
            assert result.success is False
            assert "Validation error" in result.error
    
    @patch('your_module.logging')
    def test_error_logging(self, mock_logging):
        """Test that errors are properly logged."""
        process_data(None)
        assert mock_logging.error.called or mock_logging.info.called
    
    @pytest.mark.asyncio
    async def test_async_operations(self):
        """Test async operation handling."""
        result = await process_async_data({"id": "123"})
        assert result.success is True
```

## TypeScript Testing (Vitest)

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { processData } from './dataProcessing';

describe('processData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should process valid data successfully', async () => {
    const result = await processData({ id: '123', email: 'test@example.com' });

    expect(result.success).toBe(true);
    expect(result.data).toBeDefined();
    expect(result.error).toBeUndefined();
  });

  it('should handle invalid input gracefully', async () => {
    const result = await processData({});
    
    expect(result.success).toBe(false);
    expect(result.error).toContain('Invalid input');
  });

  it('should respect timeout configuration', async () => {
    const result = await processData(
      { id: '123' },
      { timeoutMs: 100, strictMode: false }
    );

    expect(result.success).toBe(false);
  }, 200);

  it('should handle retries correctly', async () => {
    const mockProcess = vi.fn()
      .mockRejectedValueOnce(new Error('First attempt'))
      .mockResolvedValueOnce({ processed: true });

    const result = await processWithRetry(mockProcess);
    expect(mockProcess).toHaveBeenCalledTimes(2);
    expect(result.success).toBe(true);
  });
});
```

## Test Organization

| Test Type | Purpose | Location | Tools |
|-----------|---------|----------|-------|
| Unit | Individual functions/classes | `tests/unit/` | pytest, vitest |
| Integration | Component interactions | `tests/integration/` | pytest, vitest |
| E2E | Complete user workflows | `tests/e2e/` | Playwright MCP |
| Performance | Benchmarks | `tests/performance/` | locust, k6 |
| Security | Access control, input validation | `tests/security/` | custom |

## Coverage Targets

- **Business Logic**: ≥80% coverage
- **Security Functions**: 100% coverage
- **Critical Paths**: 100% coverage
- **Utility Functions**: ≥70% coverage

## Test Requirements

Every test file should include:

1. **Happy path tests**: Normal successful operations
2. **Invalid input tests**: Edge cases, nulls, wrong types
3. **Error scenario tests**: All failure modes
4. **Mock isolation**: External dependencies mocked
5. **Async handling**: Proper async/await testing
6. **Cleanup**: beforeEach/afterEach for state reset

## E2E Testing with Playwright MCP

Use the Playwright MCP tool for:
- Complete user workflow validation
- Cross-browser testing
- Visual regression testing
- Performance benchmarks

```typescript
// Example E2E test structure
test('user can complete checkout', async ({ page }) => {
  await page.goto('/products');
  await page.click('[data-testid="add-to-cart"]');
  await page.click('[data-testid="checkout"]');
  await page.fill('[name="email"]', 'test@example.com');
  await page.click('[type="submit"]');
  await expect(page.locator('.confirmation')).toBeVisible();
});
```
