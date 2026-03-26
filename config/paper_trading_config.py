"""
Paper trading configuration settings
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PaperTradingConfig:
    """Configuration for paper trading mode"""
    enabled: bool = False
    initial_balance: float = 10000.0  # Starting paper trading balance
    slippage_percent: float = 0.05    # Percentage slippage to simulate (0.05%)
    fee_percent: float = 0.075        # Fee percentage to simulate (0.075%)
    max_position_size: float = 0.1    # Maximum position size as fraction of balance
    min_order_size: float = 1.0       # Minimum order size in USD
    simulate_price_impact: bool = True # Whether to simulate price impact based on order size
    trade_log_file: Optional[str] = "logs/paper_trades.log"  # File to log paper trades