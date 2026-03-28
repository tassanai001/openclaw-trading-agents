# OpenClaw Trading Agents

**Generated:** 2026-03-28  
**Language:** Python 3.10+

## OVERVIEW

Multi-Agent Algorithmic Trading System on OpenClaw platform. 6 specialized agents (Scanner, Sentiment, Strategy, Risk, Execution, Learning) coordinate via shared SQLite state. Supertrend (60%) + Sentiment (40%) signal combination with 2% position sizing and 5% daily loss limit.

## STRUCTURE

```
openclaw-trading-agents/
├── agents/          # 6 trading agents (scanner, sentiment, strategy, risk, execution, learning)
├── config/          # Configuration (trading, agent, database, exchange)
├── tests/           # Unit & integration tests (pytest)
├── scripts/         # Setup & health check scripts
├── reports/         # Performance reports
├── documents/       # Documentation (MASTER_PLAN.md)
├── data/            # SQLite database (state.db)
└── memory/          # Daily reports & performance summaries
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Trading signal generation | `agents/scanner/scanner.py` | Supertrend + RSI + MACD indicators |
| Market sentiment | `agents/sentiment/sentiment.py` | Twitter + News + Fear & Greed Index |
| Signal combination | `agents/strategy/strategy.py` | 60/40 weighted decision |
| Risk enforcement | `agents/risk/risk.py` | 2% position, 5% daily loss, 5 max positions |
| Order execution | `agents/execution/execution_agent.py` | Adapter pattern (Binance/Hyperliquid) |
| Performance tracking | `agents/learning/learning.py` | Daily reports & metrics |
| Global config | `config/trading_config.py` | Pairs, thresholds, risk parameters |
| Database schema | `config/db_schema.py` | SQLite tables for state, positions, trades |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `Scanner` | class | `agents/scanner/scanner.py` | Technical analysis & signal detection |
| `SentimentAgent` | class | `agents/sentiment/sentiment.py` | Twitter + News sentiment analysis |
| `StrategyAgent` | class | `agents/strategy/strategy.py` | Signal combination & decision making |
| `RiskAgent` | class | `agents/risk/risk.py` | Position sizing & daily loss limits |
| `ExecutionAgent` | class | `agents/execution/execution_agent.py` | Order execution via adapters |
| `LearningAgent` | class | `agents/learning/learning.py` | Performance tracking & reporting |
| `TRADING_CONFIG` | dict | `config/trading_config.py` | Global trading configuration |
| `DB_SCHEMA` | str | `config/db_schema.py` | SQLite schema definition |

## CONVENTIONS

- **Agent patterns**: Each agent has `config.py` for configuration, `__init__.py` for exports, and main implementation file
- **Signal range**: Scanner/Sentiment signals normalized to -1.0 to 1.0
- **Decision thresholds**: LONG > 0.2, SHORT < -0.2, HOLD otherwise
- **Risk constraints**: 2% position size, 5% daily loss, 5 max open positions
- **Database**: SQLite at `data/state.db` with tables: `portfolio_state`, `positions`, `trade_log`, `performance_metrics`, `scan_cache`, `sentiment_cache`

## ANTI-PATTERNS (THIS PROJECT)

- **Never** hardcode API credentials — use environment variables
- **Never** skip circuit breakers — halt trading at extreme F&G values (<20 or >80)
- **Never** exceed daily loss limit — auto-stop at 5% loss
- **Never** open >5 positions simultaneously
- **Never** allow slippage >0.5% on execution

## UNIQUE STYLES

- **Adapter pattern** for exchange support (Binance/Hyperliquid)
- **Mock implementation fallback** when real data unavailable (scanner, sentiment)
- **Time-based seed diversity** for sentiment mock data (cyclical patterns)
- **Manual indicator calculation** (pandas-ta not yet available, Python 3.10+ requirement)

## COMMANDS

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "import sqlite3; from config.db_schema import DB_SCHEMA; conn = sqlite3.connect('data/state.db'); conn.executescript(DB_SCHEMA); conn.commit(); conn.close()"

# Run scanner agent
openclaw agent scanner

# Run full trading cycle
openclaw run trading-cycle

# Run tests
pytest tests/

# View portfolio state
sqlite3 data/state.db "SELECT * FROM portfolio_state ORDER BY timestamp DESC LIMIT 1;"

# View open positions
sqlite3 data/state.db "SELECT * FROM positions WHERE status='OPEN';"

# View recent trades
sqlite3 data/state.db "SELECT * FROM trade_log ORDER BY timestamp DESC LIMIT 10;"
```

## NOTES

- **Testnet first**: All agents default to Hyperliquid testnet
- **Paper trading**: Enable via `config/paper_trading_config.py`
- **Scan interval**: 5 minutes via cron
- **Pairs**: Top 10 crypto (BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX, TRX, LINK) / USDT
