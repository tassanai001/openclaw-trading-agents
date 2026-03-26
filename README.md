# 🚀 OpenClaw Trading Agents

Multi-Agent Algorithmic Trading System built on OpenClaw platform.

## 📋 Project Overview

| Field | Value |
|-------|-------|
| **Type** | Multi-Agent Algorithmic Trading System |
| **Platform** | OpenClaw (agents + cron + memory + tools) |
| **Exchange** | Hyperliquid Testnet → Production |
| **Pairs** | Top 10 Crypto (BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX, TRX, LINK) / USDT |
| **Strategy** | Supertrend (60%) + Sentiment (40%) |
| **Risk** | 2% per trade, 5% daily loss limit |
| **Scan Interval** | 5 minutes |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    OpenClaw Gateway                             │
├─────────────────────────────────────────────────────────────────┤
│  Cron (5m) ──┬──────────────────────────────────────┐           │
│              │                                      │           │
│              ▼                                      ▼           │
│    ┌─────────────────┐                   ┌─────────────────┐   │
│    │ Scanner Agent   │                   │ Sentiment Agent │   │
│    │ - Browser       │                   │ - Web Search    │   │
│    │ - TradingView   │                   │ - LLM Analysis  │   │
│    │ - API Fallback  │                   │ - Source Weight │   │
│    └────────┬────────┘                   └────────┬────────┘   │
│             │                                     │            │
│             └──────────────┬──────────────────────┘            │
│                            ▼                                   │
│                   ┌─────────────────┐                          │
│                   │ Strategy Agent  │                          │
│                   │ - Combine       │                          │
│                   │ - Decision      │                          │
│                   └────────┬────────┘                          │
│                            │                                   │
│                            ▼                                   │
│                   ┌─────────────────┐                          │
│                   │ Risk Agent      │                          │
│                   │ - Position Size │                          │
│                   │ - Daily Loss    │                          │
│                   └────────┬────────┘                          │
│                            │                                   │
│                            ▼                                   │
│                   ┌─────────────────┐                          │
│                   │ Execution Agent │                          │
│                   │ - Slippage Check│                          │
│                   │ - Liquidity     │                          │
│                   │ - Order         │                          │
│                   └────────┬────────┘                          │
│                            │                                   │
│                            ▼                                   │
│                   ┌─────────────────┐                          │
│                   │ Learning Agent  │                          │
│                   │ - Log Trade     │                          │
│                   │ - Performance   │                          │
│                   └─────────────────┘                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Data Layer (Hybrid)                        │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  SQLite: portfolio_state, positions, trade_log          │   │
│  │  Markdown: daily_reports, performance_summary           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
openclaw-trading-agents/
├── agents/              # 6 trading agents
│   ├── scanner/         # TradingView chart analysis
│   ├── sentiment/       # Market sentiment analysis
│   ├── strategy/        # Signal combination & decision
│   ├── risk/            # Risk management & position sizing
│   ├── execution/       # Order execution on Hyperliquid
│   └── learning/        # Performance tracking & optimization
├── data/
│   └── state.db         # SQLite database
├── memory/
│   ├── daily_reports/   # Daily performance reports
│   └── performance/     # Performance summaries
├── config/
│   ├── trading_config.py    # Global trading configuration
│   ├── agents_config.yaml   # Agent-specific settings
│   └── db_schema.py         # SQLite database schema
├── scripts/
│   ├── setup_agents.sh      # Initialize agents
│   ├── register_crons.sh    # Register cron jobs
│   └── health_check.sh      # System health check
├── logs/                # Application logs
├── tests/               # Unit & integration tests
├── documents/           # Documentation
│   └── MASTER_PLAN.md   # Full project specification
├── .gitignore
├── requirements.txt
└── README.md
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.10+
- OpenClaw installed and configured
- Hyperliquid API credentials (testnet for development)

### Installation

1. **Clone and navigate to project:**
```bash
cd /Users/nunamzza/projects/trading/openclaw-trading-agents
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Initialize database:**
```bash
python -c "import sqlite3; from config.db_schema import DB_SCHEMA; conn = sqlite3.connect('data/state.db'); conn.executescript(DB_SCHEMA); conn.commit(); conn.close()"
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

## ⚡ Quick Start

### Start Trading (Testnet)

```bash
# Run scanner agent
openclaw agent scanner

# Run full trading cycle
openclaw run trading-cycle
```

### Check Status

```bash
# View portfolio state
sqlite3 data/state.db "SELECT * FROM portfolio_state ORDER BY timestamp DESC LIMIT 1;"

# View open positions
sqlite3 data/state.db "SELECT * FROM positions WHERE status='OPEN';"

# View recent trades
sqlite3 data/state.db "SELECT * FROM trade_log ORDER BY timestamp DESC LIMIT 10;"
```

## 🎯 Features

### Core Features
- ✅ 6 Expert Agents (Scanner, Sentiment, Strategy, Risk, Execution, Learning)
- ✅ Multi-pair scanning (Top 10 crypto pairs)
- ✅ Supertrend indicator (vision + API fallback)
- ✅ Sentiment analysis (Twitter + News + LLM)
- ✅ Signal combination (60/40 weight)
- ✅ Position sizing (2% per trade)
- ✅ Daily loss limit (5%)
- ✅ Stop-loss & Take-profit
- ✅ Trade logging (SQLite)
- ✅ Performance tracking

### Advanced Features
- ✅ SQLite database for state management
- ✅ Parallel processing (Scanner + Sentiment)
- ✅ Slippage validation before execution
- ✅ Liquidity check before execution
- ✅ API Fallback (pandas-ta)
- ✅ LLM sentiment analysis
- ✅ Source weighting
- ✅ Paper trading mode
- ✅ Circuit breakers
- ✅ Health checks

### Monitoring & Reporting
- ✅ Real-time alerts (Telegram)
- ✅ Daily performance report
- ✅ Weekly summary
- ✅ Trade history export
- ✅ P&L tracking
- ✅ Win rate analytics
- ✅ Drawdown monitoring

## 📊 Database Schema

### Tables

| Table | Purpose |
|-------|---------|
| `portfolio_state` | Current balance, margin, daily P&L |
| `positions` | Open and closed positions |
| `trade_log` | Complete trade history |
| `performance_metrics` | Daily/weekly performance stats |
| `scan_cache` | Latest scan results |
| `sentiment_cache` | Latest sentiment analysis |

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/test_integration.py -v
```

## 📝 Documentation

- [`MASTER_PLAN.md`](documents/MASTER_PLAN.md) — Full project specification
- [`AGENTS.md`](agents/README.md) — Agent details and responsibilities
- [`API_REFS.md`](documents/API_REFS.md) — API reference documentation

## ⚠️ Safety Features

- **Daily Loss Limit:** Trading stops at 5% daily loss
- **Position Limits:** Maximum 5 open positions
- **Slippage Check:** Orders rejected if slippage > 0.5%
- **Liquidity Check:** Orders rejected if insufficient liquidity
- **Circuit Breakers:** Auto-pause on API failures or unusual P&L

## 📅 Development Timeline

| Week | Phase | Status |
|------|-------|--------|
| 1 | Foundation (Agents + SQLite + Config) | 🟢 In Progress |
| 2 | Integration (Cron + Coordination) | ⚪ Planned |
| 3 | Testing (Unit + Safety + Paper Trading) | ⚪ Planned |
| 4 | Deployment (Production + Optimization) | ⚪ Planned |

## 🤝 Contributing

1. Read [`MASTER_PLAN.md`](documents/MASTER_PLAN.md) for full specification
2. Follow the established patterns in existing agents
3. Write tests for new features
4. Update documentation as needed

## 📄 License

MIT

---

**Last Updated:** 2026-03-21  
**Status:** Day 1 Setup Complete
