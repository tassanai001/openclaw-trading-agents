# Tests

**Generated:** 2026-03-28  
**Language:** Python 3.10+

## OVERVIEW

Pytest-based test suite with fixtures and async support. Configuration in `conftest.py`.

## STRUCTURE

```
tests/
├── conftest.py      # Pytest fixtures & path setup
└── adapters/        # Adapter-specific tests
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Test fixtures | `conftest.py` | pytest fixtures, path setup |
| Adapter tests | `tests/adapters/` | Exchange-specific tests |

## CONVENTIONS

- **Test runner**: `pytest tests/`
- **Async support**: pytest-asyncio
- **Path setup**: Root added to `sys.path` in `conftest.py`

## ANTI-PATTERNS

- **Never** test without fixtures — use shared test data
- **Never** skip async fixtures for async code
