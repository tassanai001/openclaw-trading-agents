# Configuration

**Generated:** 2026-03-28  
**Language:** Python 3.10+

## OVERVIEW

Centralized configuration for trading parameters, agent settings, database schema, and exchange credentials.

## STRUCTURE

```
config/
├── trading_config.py       # Global trading parameters
├── agents_config.yaml      # Agent-specific settings (if exists)
├── db_schema.py            # SQLite schema definition
├── db.py                   # Database connection utilities
├── exchange_config.py      # Exchange credentials
├── paper_trading_config.py # Paper trading mode settings
├── db_logger.py            # Database logging utilities
└── orchestrator_config.py  # Orchestrator settings
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
