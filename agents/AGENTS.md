# Trading Agents

**Generated:** 2026-03-28  
**Language:** Python 3.10+

## OVERVIEW

6 specialized trading agents coordinate via shared SQLite state. Each agent handles a single responsibility: market scanning, sentiment analysis, signal combining, risk enforcement, order execution, or performance tracking.

## STRUCTURE

```
agents/
├── scanner/      # Technical analysis & signal detection
├── sentiment/    # Market sentiment analysis (Twitter + News)
├── strategy/     # Signal combination & decision making
├── risk/         # Risk management & position sizing
├── execution/    # Order execution (adapter pattern)
└── learning/     # Performance tracking & reporting
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Technical indicators | `scanner/scanner.py` | Supertrend, RSI, MACD, MA, EMA |
| Sentiment scoring | `sentiment/sentiment.py` | Twitter (40%) + News (60%) + F&G |
| Decision logic | `strategy/strategy.py` | 60/40 weighted signal combination |
| Risk checks | `risk/risk.py` | 2% position, 5% daily loss, 5 max |
| Exchange execution | `execution/execution_agent.py` | Binance/Hyperliquid adapters |
| Performance reports | `learning/learning.py` | Daily reports & metrics |

## CONVENTIONS

- **Signal range**: All signals normalized to -1.0 (SELL) to 1.0 (BUY)
- **Decision thresholds**: LONG > 0.2, SHORT < -0.2, HOLD otherwise
- **Config pattern**: Each agent has `config.py` with config dict/class
- **Export pattern**: `__init__.py` exports main class + config

## UNIQUE STYLES

- **Manual indicators**: Supertrend/RSI/MACD implemented without pandas-ta
- **Mock fallback**: Real data unavailable → deterministic mock data
- **Adapter pattern**: Exchange support via unified interface

## ANTI-PATTERNS

- **Never** hardcode API keys — use environment variables
- **Never** skip circuit breakers — halt at F&G < 20 or > 80
- **Never** exceed 5% daily loss or 5 open positions
