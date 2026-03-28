# Configuration

**Generated:** 2026-03-28  
**Language:** Python 3.10+

## OVERVIEW

Centralized configuration for trading parameters, agent settings, database schema, and exchange credentials.

## STRUCTURE

```
config/
├── trading_config.py       # Global trading parameters (pairs, thresholds, risk)
├── agents_config.yaml      # Agent-specific settings (scanner, sentiment, strategy, risk, execution, learning)
├── db_schema.py            # SQLite schema definition (portfolio_state, positions, trade_log, etc.)
├── db.py                   # Database connection utilities and wrapper
├── exchange_config.py      # Exchange credentials loading from environment variables
├── paper_trading_config.py # Paper trading mode settings and mock execution
├── db_logger.py            # Database logging utilities for trade history
└── orchestrator_config.py  # OpenClaw orchestrator settings and cron integration
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Trading params | `trading_config.py:TRADING_CONFIG` | Pairs, timeframes, thresholds |
| Risk params | `trading_config.py:TRADING_CONFIG['risk']` | Position, loss, slippage |
| Signal weights | `trading_config.py:TRADING_CONFIG['strategy_weights']` | 60/40 scanner/sentiment |
| Database schema | `db_schema.py:DB_SCHEMA` | SQLite CREATE statements |
| Exchange creds | `exchange_config.py` | Environment variable loading |

## CONVENTIONS

- **Environment variables**: API keys loaded via `os.getenv()`
- **Config pattern**: Dict-based for trading, dataclass for agents
- **Database**: SQLite at `data/state.db`

## ANTI-PATTERNS

- **Never** commit API keys — use `.env.example` template
- **Never** hardcode credentials — always use environment variables
