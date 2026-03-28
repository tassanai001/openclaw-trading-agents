"""
Configuration for Execution Agent
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionConfig:
    """Configuration for the execution agent"""
    api_key: Optional[str] = None
    secret: Optional[str] = None
    is_testnet: bool = True
    base_url: str = "https://api.hyperliquid-testnet.xyz"
    mock_mode: bool = False
    order_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    paper_trading: bool = False
    use_real_validation: bool = True
    max_slippage_percent: float = 0.5
    min_liquidity_usd: float = 50000.0