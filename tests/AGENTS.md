# Tests

**Generated:** 2026-03-28  
**Language:** Python 3.10+

## OVERVIEW

Pytest-based test suite with fixtures and async support. Configuration in `conftest.py`.

## STRUCTURE

```
tests/
├── conftest.py              # Pytest configuration with path setup
├── test_integration.py      # Full 6-agent trading cycle integration test
├── test_safety.py           # Safety circuit breakers and risk limits
├── test_db.py               # Database operations and state management
├── test_risk.py             # Risk agent validation and limits
└── adapters/                # Exchange adapter-specific tests (binance, hyperliquid)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Test configuration | `conftest.py` | pytest fixtures, path setup |
| Full trading cycle | `test_integration.py` | End-to-end 6-agent workflow |
| Safety features | `test_safety.py` | Circuit breakers, risk limits, emergency stop |
| Database operations | `test_db.py` | State management, positions, trades |
| Risk validation | `test_risk.py` | Position sizing, daily loss, max positions |
| Exchange adapters | `tests/adapters/` | Binance/Hyperliquid specific functionality |

## CONVENTIONS

- **Test runner**: `pytest tests/`
- **Async support**: pytest-asyncio
- **Path setup**: Root added to `sys.path` in `conftest.py`

## ANTI-PATTERNS

- **Never** test without fixtures — use shared test data
- **Never** skip async fixtures for async code
