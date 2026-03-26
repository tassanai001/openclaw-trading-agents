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
        "logs": "memory/*.md"
    },
    "execution": {
        "dry_run": False,  # True for paper trading
        "validate_slippage": True,
        "check_liquidity": True
    }
}
