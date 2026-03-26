# 🚀 OpenClaw Trading Agents - Master Plan

**Created:** 2026-03-21 12:26 (Asia/Bangkok)  
**Last Updated:** 2026-03-21 13:24 (Asia/Bangkok)  
**Status:** Planning Phase  
**Version:** 2.0 (Merged)

---

## 📋 Project Overview

| Field | Value |
|-------|-------|
| **Name** | `openclaw-trading-agents` |
| **Path** | `/Users/nunamzza/projects/trading/openclaw-trading-agents` |
| **Type** | Multi-Agent Algorithmic Trading System |
| **Platform** | OpenClaw (agents + cron + memory + tools) |
| **Exchange** | Hyperliquid Testnet → Production |
| **Pairs** | Top 10 Crypto (BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX, TRX, LINK) / USDT |
| **Strategy** | Supertrend (60%) + Sentiment (40%) |
| **Risk** | 2% per trade, 5% daily loss limit |
| **Scan Interval** | 5 minutes |

---

## 🎯 System Architecture

### Optimized Parallel Flow (Recommended)

```
┌─────────────────────────────────────────────────────────────────┐
│                    OpenClaw Gateway                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
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
│  │  Redis:  real-time prices, signals (cache)              │   │
│  │  MD:     daily_reports, performance_summary (human)     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Telegram Alerts ←─────────────────────────────────────────     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Weaknesses & Mitigations (จุดด้อยและแนวทางแก้ไข)

### 1. Vision Reliability (ความเปราะบางของ UI)

| Aspect | Details |
|--------|---------|
| **ปัญหา** | Browser Automation อ่านกราฟเสี่ยงพังถ้า TradingView เปลี่ยน UI หรือเน็ตช้า |
| **ผลกระทบ** | ⚠️ **HIGH** — System downtime |
| **แก้ไข** | มี **API Fallback** — ดึง OHLCV มาคำนวณ Supertrend เองด้วย `pandas-ta` |

---

### 2. State Management & Race Conditions

| Aspect | Details |
|--------|---------|
| **ปัญหา** | ไฟล์ `.md` เก็บ State อาจเกิด File Locking / ข้อมูลทับซ้อน |
| **ผลกระทบ** | ⚠️ **CRITICAL** — ข้อมูลยอดเงิน/Position อาจผิดเพี้ยน |
| **แก้ไข** | ใช้ **SQLite** สำหรับ state, **Markdown** สำหรับ human-readable logs |

---

### 3. Latency (ความหน่วง)

| Aspect | Details |
|--------|---------|
| **ปัญหา** | Sequential flow ใช้เวลา 1-3 นาที ราคาอาจเปลี่ยน |
| **ผลกระทบ** | ⚠️ **MEDIUM** — Slippage, ได้ราคาไม่ดี |
| **แก้ไข** | **Parallel Processing** — Scanner + Sentiment ทำงานพร้อมกัน |

---

### 4. Sentiment Noise

| Aspect | Details |
|--------|---------|
| **ปัญหา** | Scrap Twitter/News เจอ Spam/ข่าวปลอมเยอะ |
| **ผลกระทบ** | ⚠️ **MEDIUM** — ตัดสินใจผิดจากข้อมูลผิด |
| **แก้ไข** | ใช้ **LLM** วิเคราะห์ + **Source Weighting** |

---

## 🏗️ Phase 1: Foundation (Week 1)

### **Day 1-2: Project Setup**

#### 1.1 Directory Structure

```
openclaw-trading-agents/
├── agents/
│   ├── scanner/
│   │   ├── agent.py              # Main scanner logic
│   │   ├── tradingview_watcher.py # Browser automation
│   │   ├── api_fallback.py       # Pandas-TA Supertrend (fallback)
│   │   └── prompts.py            # Vision prompts for chart analysis
│   ├── sentiment/
│   │   ├── agent.py
│   │   ├── twitter_scraper.py
│   │   ├── news_fetcher.py
│   │   ├── analyzer.py           # NLP sentiment scoring
│   │   └── llm_analyzer.py       # LLM-based analysis
│   ├── strategy/
│   │   ├── agent.py
│   │   ├── signal_engine.py      # Combine signals
│   │   └── decision_tree.py      # LONG/SHORT/WAIT logic
│   ├── risk/
│   │   ├── agent.py
│   │   ├── position_calculator.py
│   │   └── risk_manager.py       # Daily loss, exposure checks
│   ├── execution/
│   │   ├── agent.py
│   │   ├── hyperliquid_api.py    # API wrapper
│   │   ├── order_manager.py      # Order tracking
│   │   └── validator.py          # Slippage & liquidity check
│   └── learning/
│       ├── agent.py
│       ├── performance_analyzer.py
│       └── model_updater.py      # Strategy optimization
├── data/
│   ├── state.db                  # SQLite database
│   └── cache/                    # Redis dump (if used)
├── memory/
│   ├── daily_report_YYYY-MM-DD.md
│   ├── weekly_summary.md
│   └── performance_report.md
├── config/
│   ├── trading_config.py         # Global config
│   ├── agents_config.yaml        # Agent-specific settings
│   ├── db_schema.py              # SQLite schemas
│   └── secrets.env               # API keys (gitignore)
├── scripts/
│   ├── setup_agents.sh           # Initialize agents
│   ├── register_crons.sh         # Register cron jobs
│   ├── init_db.sh                # Initialize SQLite
│   ├── backup_db.sh              # Backup database
│   └── health_check.sh           # System health check
├── logs/
│   ├── scanner.log
│   ├── sentiment.log
│   ├── strategy.log
│   ├── risk.log
│   ├── execution.log
│   └── learning.log
├── tests/
│   ├── test_scanner.py
│   ├── test_sentiment.py
│   ├── test_strategy.py
│   ├── test_risk.py
│   ├── test_execution.py
│   └── test_integration.py
├── documents/
│   ├── MASTER_PLAN.md            # This file
│   └── API_REFS.md               # API references
├── .gitignore
├── .env.example
├── requirements.txt
└── README.md
```

---

#### 1.2 Configuration Files

**config/trading_config.py:**
```python
TRADING_CONFIG = {
    "pairs": [
        "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
        "ADA/USDT", "DOGE/USDT", "AVAX/USDT", "TRX/USDT", "LINK/USDT"
    ],
    "timeframe": "15m",
    "supertrend_period": 10,
    "supertrend_multiplier": 3,
    "strategy_weights": {
        "supertrend": 0.6,
        "sentiment": 0.4
    },
    "risk": {
        "max_position_size_pct": 0.02,  # 2% per trade
        "max_daily_loss_pct": 0.05,     # 5% daily loss
        "max_open_positions": 5,        # Increased for 10 pairs
        "stop_loss_pct": 0.03,          # 3% SL
        "take_profit_pct": 0.06,        # 6% TP
        "max_slippage_pct": 0.005       # 0.5% max slippage
    },
    "scan_interval_minutes": 5,
    "exchange": "hyperliquid_testnet",
    "storage": {
        "state_db": "sqlite:///data/state.db",
        "cache": "redis://localhost:6379",
        "logs": "memory/*.md"
    },
    "execution": {
        "dry_run": False,  # True for paper trading
        "validate_slippage": True,
        "check_liquidity": True
    }
}
```

---

**config/agents_config.yaml:**
```yaml
agents:
  scanner:
    enabled: true
    cron: "*/5 * * * *"  # Every 5 minutes
    timeout_seconds: 60
    retry_count: 3
    use_api_fallback: true  # Use pandas-ta if browser fails
    
  sentiment:
    enabled: true
    parallel: true  # Run parallel with scanner
    sources:
      - twitter:
          accounts: ["elonmusk", "realDonaldTrump", "VitalikButerin"]
          weight: 0.8
      - news:
          sites: ["coindesk.com", "cointelegraph.com", "decrypt.co"]
          weight: 0.7
    use_llm: true  # Use LLM for analysis
    timeout_seconds: 90
    
  strategy:
    enabled: true
    min_confidence: 0.7
    timeout_seconds: 30
    
  risk:
    enabled: true
    check_daily_loss: true
    check_exposure: true
    timeout_seconds: 15
    
  execution:
    enabled: true
    dry_run: false
    validate_slippage: true
    max_slippage_pct: 0.005
    check_liquidity: true
    timeout_seconds: 30
    
  learning:
    enabled: true
    review_interval: "daily"
    optimize_interval: "weekly"

database:
  type: sqlite
  path: data/state.db
  tables:
    - portfolio_state
    - positions
    - trade_log
    - performance_metrics

notifications:
  telegram:
    enabled: true
    bot_token: "${TELEGRAM_BOT_TOKEN}"
    chat_id: "${TELEGRAM_CHAT_ID}"
    alert_on:
      - trade_executed
      - risk_limit_hit
      - slippage_warning
      - daily_report
      - error
```

---

#### 1.3 Database Schema (SQLite)

**config/db_schema.py:**
```python
DB_SCHEMA = """
-- Portfolio State Table
CREATE TABLE IF NOT EXISTS portfolio_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_balance REAL NOT NULL,
    available_margin REAL NOT NULL,
    daily_pnl REAL DEFAULT 0.0,
    daily_pnl_pct REAL DEFAULT 0.0,
    open_positions INTEGER DEFAULT 0,
    daily_loss_pct REAL DEFAULT 0.0
);

-- Positions Table
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pair TEXT NOT NULL,
    side TEXT NOT NULL,  -- LONG or SHORT
    size REAL NOT NULL,
    entry_price REAL NOT NULL,
    current_price REAL,
    unrealized_pnl REAL,
    stop_loss REAL,
    take_profit REAL,
    opened_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    closed_at DATETIME,
    status TEXT DEFAULT 'OPEN'  -- OPEN or CLOSED
);

-- Trade Log Table
CREATE TABLE IF NOT EXISTS trade_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    pair TEXT NOT NULL,
    side TEXT NOT NULL,
    size REAL NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL,
    pnl REAL,
    pnl_pct REAL,
    status TEXT,  -- FILLED, CANCELLED, REJECTED
    order_id TEXT,
    reason TEXT  # Rejection reason if any
);

-- Performance Metrics Table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    total_trades INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    win_rate REAL DEFAULT 0.0,
    total_pnl REAL DEFAULT 0.0,
    best_trade REAL,
    worst_trade REAL,
    avg_win REAL,
    avg_loss REAL,
    max_drawdown REAL,
    sharpe_ratio REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Scan Results Cache
CREATE TABLE IF NOT EXISTS scan_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    pair TEXT NOT NULL,
    signal TEXT NOT NULL,  -- LONG, SHORT, WAIT
    confidence REAL,
    price REAL,
    supertrend_value REAL
);

-- Sentiment Cache
CREATE TABLE IF NOT EXISTS sentiment_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT,
    content_hash TEXT,
    sentiment_score REAL,
    sentiment_label TEXT,  -- BULLISH, BEARISH, NEUTRAL
    credibility_weight REAL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_trade_log_timestamp ON trade_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_date ON performance_metrics(date);
"""
```

---

### **Day 3-4: Core Agents Development**

#### 1.4 Scanner Agent

**Responsibility:** Scan TradingView charts for Supertrend signals

**Features:**
- Browser automation (TradingView)
- Screenshot capture
- Vision-based Supertrend reading
- **API Fallback (pandas-ta)** ← NEW
- Multi-pair scanning (10 pairs)

**OpenClaw Tools:** `browser`, `web_fetch` (API), `write`, `database`

**Input:** None (triggered by cron)

**Output:** `scan_cache` (SQLite), `memory/scan_result.md` (human-readable)

**Example Output:**
```markdown
# Scan Result - 2026-03-21 12:00

| Pair | Signal | Confidence | Price |
|------|--------|------------|-------|
| BTC/USDT | LONG | 0.85 | $67,890 |
| ETH/USDT | WAIT | 0.50 | $3,450 |
| BNB/USDT | SHORT | 0.75 | $412 |
| SOL/USDT | LONG | 0.80 | $145 |
| XRP/USDT | WAIT | 0.55 | $0.52 |
| ADA/USDT | SHORT | 0.70 | $0.58 |
| DOGE/USDT | LONG | 0.65 | $0.08 |
| AVAX/USDT | WAIT | 0.60 | $35 |
| TRX/USDT | LONG | 0.72 | $0.12 |
| LINK/USDT | SHORT | 0.68 | $18 |

Method: Browser (TradingView) + API Fallback Verified ✅
```

---

#### 1.5 Sentiment Agent

**Responsibility:** Analyze market sentiment from Twitter & News

**Features:**
- Twitter/X scraping (via web_search)
- News fetching (web_fetch)
- **LLM-based analysis** ← NEW
- **Source Weighting** ← NEW
- Filter old vs new news

**OpenClaw Tools:** `web_search`, `web_fetch`, `sessions_spawn` (LLM)

**Input:** None (triggered parallel with scanner)

**Output:** `sentiment_cache` (SQLite), `memory/sentiment_result.md`

**Example Output:**
```markdown
# Sentiment Analysis - 2026-03-21 12:00

## Overall Score: 0.72 (BULLISH)

## Sources:
| Source | Content | Sentiment | Weight | Final Score |
|--------|---------|-----------|--------|-------------|
| Elon Musk | "Bitcoin to the moon!" | Bullish (0.9) | 0.8 | 0.72 |
| CoinDesk | Market analysis | Neutral (0.5) | 0.7 | 0.35 |
| CoinTelegraph | Adoption news | Bullish (0.8) | 0.7 | 0.56 |

## Weighted Score: 0.72
## LLM Analysis: News is FRESH, affects BTC directly
```

---

#### 1.6 Strategy Agent

**Responsibility:** Combine signals and make trading decision

**Features:**
- Signal combination logic
- Confidence calculation
- LONG/SHORT/WAIT decision
- Conflict resolution

**OpenClaw Tools:** `read` (database), `write`

**Input:** `scan_cache`, `sentiment_cache` (SQLite)

**Output:** `trade_decision` (SQLite), `memory/trade_decision.md`

**Decision Logic:**
```python
def make_decision(scan_signal, sentiment_score):
    # Supertrend: LONG=1, SHORT=-1, WAIT=0
    supertrend_score = scan_signal  # -1 to 1
    
    # Sentiment: -1 (Bearish) to 1 (Bullish)
    sentiment_normalized = (sentiment_score * 2) - 1
    
    # Combined: 60% Supertrend + 40% Sentiment
    combined = (supertrend_score * 0.6) + (sentiment_normalized * 0.4)
    
    # Threshold: >0.4 = LONG, <-0.4 = SHORT, else WAIT
    if combined > 0.4:
        return "LONG", abs(combined)
    elif combined < -0.4:
        return "SHORT", abs(combined)
    else:
        return "WAIT", abs(combined)
```

---

#### 1.7 Risk Agent

**Responsibility:** Validate trades against risk rules

**Features:**
- Position size calculation
- Daily loss tracking (from SQLite)
- Exposure limits
- Portfolio health check

**OpenClaw Tools:** `read` (database), `edit`, `write`

**Input:** `trade_decision`, `portfolio_state` (SQLite)

**Output:** `risk_approval` (SQLite), `memory/risk_approval.md`

**Risk Checks:**
```python
def validate_risk(decision, portfolio):
    checks = {
        "daily_loss": portfolio.daily_loss_pct < 0.05,  # < 5%
        "exposure": portfolio.open_positions < 5,        # < 5 positions
        "margin": portfolio.available_margin > decision.size
    }
    
    if all(checks.values()):
        position_size = portfolio.total_balance * 0.02  # 2%
        return {"approved": True, "size": position_size}
    else:
        return {"approved": False, "reason": "Risk limit exceeded"}
```

---

#### 1.8 Execution Agent

**Responsibility:** Execute trades on Hyperliquid

**Features:**
- Hyperliquid API integration
- **Slippage Validation** ← NEW
- **Liquidity Check** ← NEW
- Order placement (LONG/SHORT)
- Order status tracking
- Telegram alerts

**OpenClaw Tools:** `exec` (curl), `message`, `write` (database)

**Input:** `risk_approval` (SQLite)

**Output:** `trade_log` (SQLite), `memory/trade_log.md`, Telegram alert

**Execution Flow:**
```python
def execute(risk_approval):
    # Step 1: Get real-time price
    real_price = hyperliquid.get_price(risk_approval["pair"])
    
    # Step 2: Check slippage
    expected_price = risk_approval["expected_price"]
    slippage = abs(real_price - expected_price) / expected_price
    
    if slippage > 0.005:  # > 0.5%
        return {"status": "REJECTED", "reason": f"High slippage: {slippage:.2%}"}
    
    # Step 3: Check liquidity
    order_book = hyperliquid.get_order_book(risk_approval["pair"])
    liquidity = order_book["bid_volume"] if risk_approval["side"] == "LONG" else order_book["ask_volume"]
    
    if liquidity < risk_approval["size"]:
        return {"status": "REJECTED", "reason": "Low liquidity"}
    
    # Step 4: Place order
    order = hyperliquid.place_order(
        pair=risk_approval["pair"],
        side=risk_approval["side"],
        size=risk_approval["size"]
    )
    
    # Step 5: Log to database
    db.execute("INSERT INTO trade_log ...")
    
    # Step 6: Send Telegram alert
    telegram.send(f"✅ {risk_approval['side']} {risk_approval['pair']} @ ${real_price}")
    
    return {"status": "FILLED", "order_id": order.id, "price": real_price}
```

---

#### 1.9 Learning Agent

**Responsibility:** Track performance and provide feedback

**Features:**
- Trade logging (from SQLite)
- Performance tracking
- Win/loss analysis
- Strategy feedback loop
- Daily/Weekly reports

**OpenClaw Tools:** `read` (database), `write` (memory files), `message` (Telegram)

**Input:** `trade_log`, `performance_metrics` (SQLite)

**Output:** `performance_metrics` (updated), `memory/daily_report.md`, Telegram report

---

## 🏗️ Phase 2: Integration (Week 2)

### **Day 8-9: Cron Jobs Setup**

#### 2.1 Cron Jobs Schedule

| Job | Schedule | Agent | Purpose |
|-----|----------|-------|---------|
| `scan-market` | Every 5 min | Scanner + Sentiment (Parallel) | Scan TradingView + Sentiment |
| `strategy-review` | Every 15 min | Strategy | Review signals |
| `hourly-review` | Every 1 hour | All | System review |
| `daily-report` | 23:00 daily | Learning | Daily P&L report |
| `weekly-optimize` | 09:00 Sunday | Strategy+Learning | Optimize params |

#### 2.2 Cron Job Configuration

```python
CRON_JOBS = [
    {
        "name": "scan-market",
        "schedule": {"kind": "every", "everyMs": 300000},  # 5 min
        "payload": {
            "kind": "agentTurn",
            "message": "Run Scanner + Sentiment Agents (parallel)"
        },
        "sessionTarget": "isolated"
    },
    {
        "name": "daily-report",
        "schedule": {"kind": "cron", "expr": "0 23 * * *", "tz": "Asia/Bangkok"},
        "payload": {
            "kind": "agentTurn",
            "message": "Run Learning Agent: generate daily performance report"
        },
        "sessionTarget": "isolated",
        "delivery": {"mode": "announce", "channel": "telegram"}
    }
]
```

---

### **Day 10-11: Database & Memory System**

#### 2.2 Hybrid Memory System

**SQLite (Real-time State):**
- `portfolio_state` — Current balance, P&L, positions
- `positions` — Open/closed positions
- `trade_log` — All trades (executed)
- `performance_metrics` — Daily/weekly stats
- `scan_cache` — Latest scan results
- `sentiment_cache` — Latest sentiment

**Markdown Files (Human-Readable):**
- `memory/daily_report_YYYY-MM-DD.md` — Daily summary
- `memory/weekly_summary.md` — Weekly performance
- `memory/performance_report.md` — Overall metrics

---

### **Day 12-14: Agent Coordination**

#### 2.3 Parallel Orchestration

```python
# agents/orchestrator.py
import asyncio
import sqlite3

async def run_trading_cycle():
    # Step 1: Run Scanner & Sentiment in PARALLEL
    scan_result, sentiment_result = await asyncio.gather(
        scanner_agent.run(),
        sentiment_agent.run(),
        return_exceptions=True
    )
    
    # Step 2: Write to SQLite
    db = sqlite3.connect('data/state.db')
    db.execute("INSERT INTO scan_cache ...", scan_result)
    db.execute("INSERT INTO sentiment_cache ...", sentiment_result)
    db.commit()
    
    # Step 3: Strategy
    decision = strategy_agent.run(scan_result, sentiment_result)
    db.execute("INSERT INTO trade_decision ...", decision)
    db.commit()
    
    # Step 4: Risk
    risk_approval = risk_agent.run(decision)
    db.execute("INSERT INTO risk_approval ...", risk_approval)
    db.commit()
    
    # Step 5: Execute (if approved)
    if risk_approval["approved"]:
        trade_result = execution_agent.run(risk_approval)
        db.execute("INSERT INTO trade_log ...", trade_result)
        db.commit()
        
        # Step 6: Learn
        learning_agent.update_performance(trade_result)
        db.commit()
```

---

## 🏗️ Phase 3: Testing & Safety (Week 3)

### **Day 15-17: Testing**

#### 3.1 Test Types

| Test Type | Scope | Tools |
|-----------|-------|-------|
| Unit Tests | Individual agents | pytest, unittest |
| Integration Tests | Full cycle | pytest, mock APIs |
| Database Tests | SQLite operations | pytest, sqlite3 |
| Paper Trading | Live simulation | Dry run mode |

#### 3.2 Paper Trading Mode

```python
# config/trading_config.py
"execution": {
    "dry_run": True,  # No real orders
    "log_to_db": True,  # Still log to database
    "simulate_slippage": True,
    "simulate_liquidity": True
}
```

---

### **Day 18-19: Safety Features**

#### 3.3 Circuit Breakers

| Condition | Action |
|-----------|--------|
| Daily loss > 80% | Warning alert (Telegram) |
| Daily loss > 100% | **Stop trading** (auto-pause) |
| API failure (3x) | Pause + alert |
| Slippage > 1% | Reject order + log |
| Unusual P&L | Pause + notify |

#### 3.4 Alert Conditions

```python
ALERT_CONDITIONS = [
    "trade_executed",
    "risk_limit_warning",  # 80% of daily loss
    "risk_limit_hit",      # 100% of daily loss
    "slippage_warning",    # > 0.5%
    "api_error",
    "daily_report",
    "weekly_summary"
]
```

---

### **Day 20-21: Documentation**

#### 3.5 Required Docs

- `README.md` — Project overview, setup, quick start
- `MASTER_PLAN.md` — This file (full plan)
- `API_REFS.md` — Hyperliquid API reference
- `TROUBLESHOOTING.md` — Common issues and fixes
- `CHANGELOG.md` — Version history

---

## 🏗️ Phase 4: Deployment (Week 4)

### **Day 22-23: Production Prep**

#### 4.1 Environment Variables

```bash
# .env
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=8062364760
HYPERLIQUID_API_KEY=xxx
HYPERLIQUID_API_SECRET=xxx
OPENAI_API_KEY=xxx  # For vision analysis (optional)
```

#### 4.2 Health Check Script

```bash
# scripts/health_check.sh
# - Check all agents alive
# - Check API connectivity (Hyperliquid, TradingView)
# - Check database valid (SQLite integrity)
# - Check cron jobs registered
# - Check disk space
```

---

### **Day 24-25: Soft Launch**

#### 4.3 Testnet Deployment Checklist

- [ ] All API keys configured
- [ ] Telegram bot tested
- [ ] All cron jobs registered
- [ ] Database initialized (SQLite)
- [ ] Health check passing
- [ ] Alerts working
- [ ] Paper trading validated (100+ cycles)

---

### **Day 26-28: Optimization**

#### 4.4 Performance Review

- Analyze trade history (from SQLite)
- Tune Supertrend parameters
- Adjust sentiment weights
- Optimize risk limits
- Review slippage statistics

---

## 📊 Full Feature List

### ✅ Core Features
- [ ] 6 Expert Agents (Scanner, Sentiment, Strategy, Risk, Execution, Learning)
- [ ] Multi-pair scanning (Top 10 crypto pairs)
- [ ] Supertrend indicator (vision + API fallback)
- [ ] Sentiment analysis (Twitter + News + LLM)
- [ ] Signal combination (60/40 weight)
- [ ] Position sizing (2% per trade)
- [ ] Daily loss limit (5%)
- [ ] Stop-loss & Take-profit
- [ ] Telegram alerts
- [ ] Trade logging (SQLite)
- [ ] Performance tracking

### ✅ Advanced Features
- [ ] **SQLite database** for state management ← NEW
- [ ] **Parallel processing** (Scanner + Sentiment) ← NEW
- [ ] **Slippage validation** before execution ← NEW
- [ ] **Liquidity check** before execution ← NEW
- [ ] **API Fallback** (pandas-ta) ← NEW
- [ ] **LLM sentiment analysis** ← NEW
- [ ] **Source weighting** ← NEW
- [ ] Paper trading mode
- [ ] Circuit breakers
- [ ] Health checks
- [ ] Auto-retry on failures
- [ ] Parameter optimization (weekly)

### ✅ Monitoring & Reporting
- [ ] Real-time Telegram alerts
- [ ] Daily performance report
- [ ] Weekly summary
- [ ] Trade history export (SQLite query)
- [ ] P&L tracking
- [ ] Win rate analytics
- [ ] Drawdown monitoring

---

## 📅 Timeline Summary

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Foundation | 6 Agents + SQLite + Config + Parallel orchestration |
| 2 | Integration | Cron jobs + Database + Coordination |
| 3 | Testing | Unit tests + Safety + Docs + Paper trading |
| 4 | Deployment | Production setup + Optimization |

---

## 🎯 Pre-Launch Checklist

- [ ] All API keys configured and tested
- [ ] Telegram bot tested (alerts working)
- [ ] SQLite database initialized
- [ ] Paper trading mode validated (100+ cycles)
- [ ] Risk limits tested (circuit breakers work)
- [ ] Slippage validation working
- [ ] Error handling verified (API failures, network issues)
- [ ] All alerts working (trade, risk, daily report)
- [ ] Backup system ready (database backups)
- [ ] Documentation complete
- [ ] Health check script passing
- [ ] All cron jobs registered and running

---

## 🚀 Next Steps

1. **Review this plan** — อ่านและตรวจสอบรายละเอียด
2. **Approve or modify** — บอกถ้ามีอะไรอยากแก้
3. **Start building** — เริ่มสร้างโปรเจคจริง

---

**Last Updated:** 2026-03-21 13:24 (Asia/Bangkok)
