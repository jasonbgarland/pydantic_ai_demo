# Copilot / Assistant Guidelines for This Repository

## Testing

- Use unittest-style tests for new test cases.
- Prefer `unittest.TestCase` for most tests, or `unittest.IsolatedAsyncioTestCase` when async is needed.
- Place tests under `backend/tests/` and name files `test_*.py`.

### Unit Testing Strategy

- **All features should be unit tested in isolation** with external calls mocked (Redis, databases, HTTP clients, etc.)
- Use `unittest.mock` to mock external dependencies and focus on testing business logic
- Mock examples:
  - `@patch('app.main.redis_client')` for Redis calls
  - `@patch('requests.get')` for HTTP requests
  - `@patch('app.main.get_session')` for function calls

### Integration Testing

- **Interfaces can be tested** with minimal integration test files that call actual endpoints
- Integration tests should make real HTTP calls to `http://localhost:8001`
- Name integration test files `test_*_integration.py`
- Integration tests should be **toggle-able with a flag**:

  ```python
  import os
  import unittest

  @unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), 'Integration tests disabled')
  class TestSessionIntegration(unittest.TestCase):
      # Real HTTP calls here
  ```

### Testing Best Practices

- When testing API endpoints with mocks, use `httpx.AsyncClient(app=app, base_url="http://test")`
- When testing integration, use `requests` library with timeouts
- Always add timeouts to `requests` calls: `timeout=10`
- Clean up any test data created during integration tests

## Testing commands

- Run tests using the standard library test runner so contributors don't need extra test runners installed.

```bash
cd backend
# discover and run all unittest-compatible tests
python -m unittest discover -v

# Run only unit tests (skip integration tests)
python -m unittest discover -v -k "not integration"

# Run integration tests (requires services running)
RUN_INTEGRATION_TESTS=1 python -m unittest discover -v -k "integration"
```

## Code Quality

- Run pylint to maintain code quality standards:

```bash
cd backend
pylint app/ tests/
```

## Development notes

- Use Redis for ephemeral session state and Postgres for durable saves.
- Implement agents under `backend/app/agents/` using PydanticAI patterns.
- Keep changes small and focused. Update `TODO` list in `.ai/PLAN.MD` and the project todo list when starting/finishing tasks.
