# Risk Agent

**Generated:** 2026-03-28  
**Language:** Python 3.10+

## OVERVIEW

Enforces trading constraints: 2% position size, 5% daily loss limit, 5 max positions.

## STRUCTURE

```
agents/risk/
├── risk.py       # Main implementation
├── config.py     # RISK_CONFIG dict + RiskConfig class
└── __init__.py   # Exports RiskAgent class
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Position sizing | `risk.py:check_position_size()` | 2% of account |
| Daily loss limit | `risk.py:check_daily_loss_limit()` | 5% of account |
| Max positions | `risk.py:check_max_positions()` | 5 positions |
| Trade validation | `risk.py:validate_trade()` | All checks combined |

## CONVENTIONS

- **Position limit**: 2% per trade
- **Daily loss limit**: 5% of account (hard stop)
- **Max positions**: 5 simultaneous

## ANTI-PATTERNS

- **Never** override risk limits — all trades must pass `validate_trade()`
- **Never** skip daily reset at midnight
