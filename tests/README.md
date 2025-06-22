# Palitra Tests

This directory contains the test suite for the Palitra library, organized by functionality and test type.

## Structure

```
tests/
├── conftest.py                    # Common fixtures and configuration
├── core/                          # Core functionality tests
│   ├── test_event_loop_runner.py  # EventLoopThreadRunner class tests
│   └── test_global_functions.py   # Global functions (run, gather, etc.) tests
├── integration/                   # Integration tests
│   └── test_asgiref_compatibility.py  # asgiref compatibility tests
├── performance/                   # Performance and load tests
│   └── test_concurrent_operations.py  # Concurrent operation performance
├── edge_cases/                    # Edge cases and error handling
│   └── test_error_handling.py     # Error handling and edge cases
└── README.md                      # This file
```

## Test Categories

### Core Tests (`core/`)
Tests for the fundamental functionality of the library:
- **EventLoopThreadRunner**: Tests for the main class that manages asyncio event loops in background threads
- **Global Functions**: Tests for the high-level API functions (`run`, `gather`, `shutdown_global_runner`, `is_runner_alive`)

### Integration Tests (`integration/`)
Tests that verify compatibility and integration with other libraries:
- **asgiref Compatibility**: Tests ensuring palitra works correctly with asgiref's sync/async conversion functions

### Performance Tests (`performance/`)
Tests focused on performance characteristics:
- **Concurrent Operations**: Tests for concurrent execution performance, memory usage, and scalability

### Edge Cases (`edge_cases/`)
Tests for error conditions and edge cases:
- **Error Handling**: Tests for exception handling, timeout scenarios, and resource cleanup

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run specific test categories:
```bash
# Core functionality only
pytest tests/core/

# Integration tests only
pytest tests/integration/

# Performance tests only
pytest tests/performance/

# Edge cases only
pytest tests/edge_cases/
```

### Run with specific event loop policies:
```bash
# Test with default asyncio policy
pytest tests/ -k "not uvloop"

# Test with uvloop policy
pytest tests/ -k "uvloop"
```

## Test Fixtures

Common fixtures are defined in `conftest.py`:
- `event_loop_runner`: Provides EventLoopThreadRunner instances with different event loop policies
- `sample_coroutines`: Provides sample coroutines for testing
- `exception_coroutine`: Provides coroutines that raise exceptions

## Test Coverage

The test suite covers:
- ✅ Basic functionality of EventLoopThreadRunner
- ✅ Global function API
- ✅ Thread safety and concurrency
- ✅ Error handling and edge cases
- ✅ Resource cleanup and garbage collection
- ✅ Integration with asgiref
- ✅ Performance characteristics
- ✅ Timeout handling
- ✅ Exception propagation

## Adding New Tests

When adding new tests:

1. **Choose the appropriate category** based on what you're testing
2. **Use existing fixtures** from `conftest.py` when possible
3. **Follow the naming convention**: `test_<functionality>_<scenario>`
4. **Add docstrings** explaining what the test verifies
5. **Consider both success and failure cases**

### Example:
```python
def test_new_feature_basic_functionality(event_loop_runner: EventLoopThreadRunner) -> None:
    """Test basic functionality of new feature."""
    async def test_operation() -> str:
        await asyncio.sleep(0.01)
        return "result"
    
    result = event_loop_runner.run(test_operation())
    assert result == "result"
``` 