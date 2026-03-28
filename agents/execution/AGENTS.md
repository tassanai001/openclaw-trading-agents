# Execution Agent

**Generated:** 2026-03-28  
**Language:** Python 3.10+

## OVERVIEW

Order execution via adapter pattern supporting Binance and Hyperliquid. Includes paper trading mode.

## STRUCTURE

```
agents/execution/
├── execution_agent.py   # Main implementation
├── config.py            # ExecutionConfig dataclass
├── adapters/
│   ├── base.py          # ExchangeAdapter interface
│   ├── binance.py       # BinanceAdapter implementation
│   ├── hyperliquid.py   # HyperliquidAdapter implementation
│   └── __init__.py      # Exports adapters
├── models/
│   ├── order.py         # Order/OrderResult dataclasses
│   ├── position.py      # Position/Balance dataclasses
│   ├── common.py        # ExchangeCredentials, OrderSide, OrderType
│   └── __init__.py      # Exports models
└── __init__.py          # Exports ExecutionAgent
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Order placement | `execution_agent.py:place_order()` | Delegates to adapter/paper |
| Signal execution | `execution_agent.py:execute_signal()` | From signal dict |
| Paper trading | `execution_agent.py:_place_paper_order()` | Simulated execution |
| Balance/positions | `execution_agent.py:get_balance()` | Via adapter |

## CONVENTIONS

- **Adapter pattern**: Unified interface for multiple exchanges
- **Paper trading**: Enabled via `config/paper_trading_config.py`
- **Order model**: `Order`, `OrderResult` dataclasses

## ANTI-PATTERNS

- **Never** execute without adapter initialization
- **Never** skip slippage validation (max 0.5%)
