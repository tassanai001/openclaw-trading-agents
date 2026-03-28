# Scanner Agent

**Generated:** 2026-03-28  
**Language:** Python 3.10+

## OVERVIEW

Technical analysis agent detecting trading opportunities via Supertrend, RSI, MACD, MA, and EMA indicators on 5m/15m/1h/4h/1d timeframes.

## STRUCTURE

```
agents/scanner/
├── scanner.py    # Main implementation
├── config.py     # Timeframes, pairs, indicator parameters
└── __init__.py   # Exports Scanner class
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Market scanning | `scanner.py:scan_market()` | Async, multi-pair, multi-timeframe |
| Indicator calc | `scanner.py:_calculate_indicators()` | Supertrend, RSI, MACD, MA, EMA |
| Trend detection | `scanner.py:detect_trend_change()` | Supertrend direction changes |
| Signal generation | `scanner.py:get_signal()` | Normalized -1.0 to 1.0 |

## CONVENTIONS

- **Supertrend**: 10-period ATR, 3.0 multiplier
- **RSI**: 14-period
- **MACD**: 12/26/9
- **Signals**: -1.0 (SELL) to 1.0 (BUY), normalized across factors

## ANTI-PATTERNS

- **Never** skip database caching — results stored in `scan_cache` table
- **Never** return raw signals without normalization
