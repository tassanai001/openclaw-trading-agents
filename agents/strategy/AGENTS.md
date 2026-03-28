# Strategy Agent

**Generated:** 2026-03-28  
**Language:** Python 3.10+

## OVERVIEW

Combines Scanner (60%) and Sentiment (40%) signals into trading decisions. Implements circuit breakers for extreme F&G values. Production-ready with environment variable loading and validation.

## STRUCTURE

```
agents/strategy/
├── strategy.py   # Main implementation
├── config.py     # StrategyConfig dataclass + get_config()
└── __init__.py   # Exports StrategyAgent class
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Signal combine | `strategy.py:combine_signals()` | Weighted average |
| Circuit breaker | `strategy.py:check_circuit_breaker()` | F&G < 20 or > 80 |
| Decision logic | `strategy.py:make_decision()` | LONG/SHORT/WAIT |
| Position sizing | `strategy.py:calculate_position_size()` | Based on signal strength |
| Config class | `config.py:StrategyConfig` | Dataclass with validation |
| Config factory | `config.py:get_config()` | Environment variable loading |

## CONVENTIONS

- **Thresholds**: LONG > 0.2, SHORT < -0.2, WAIT in neutral zone
- **Position sizing**: 2% base, scales to 5% max based on signal strength
- **Decision range**: -1.0 to 1.0, neutral zone ±0.1
- **Signal weights**: Scanner 60%, Sentiment 40% (configurable)
- **Circuit breakers**: Halt at F&G < 20 (fear) or > 80 (greed)

## ANTI-PATTERNS

- **Never** execute without circuit breaker check
- **Never** exceed 5% position allocation
- **Never** skip signal validation when `require_both_signals=True`
- **Never** hardcode config values - use environment variables

## ENVIRONMENT VARIABLES

| Variable | Default | Description |
|----------|---------|-------------|
| `STRATEGY_SCANNER_WEIGHT` | 0.6 | Scanner signal weight |
| `STRATEGY_SENTIMENT_WEIGHT` | 0.4 | Sentiment signal weight |
| `STRATEGY_LONG_THRESHOLD` | 0.2 | Long decision threshold |
| `STRATEGY_SHORT_THRESHOLD` | -0.2 | Short decision threshold |
| `STRATEGY_BASE_POSITION_SIZE` | 0.02 | Base position size (2%) |
| `STRATEGY_MAX_POSITION_SIZE` | 0.05 | Max position size (5%) |
| `STRATEGY_FNG_FEAR` | 20 | F&G fear threshold |
| `STRATEGY_FNG_GREED` | 80 | F&G greed threshold |
