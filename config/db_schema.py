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
    reason TEXT  -- Rejection reason if any
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
