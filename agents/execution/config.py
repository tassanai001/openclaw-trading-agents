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
    mock_mode: bool = False  # Set to True for testing without real API calls
    order_timeout: int = 30  # Timeout for order execution in seconds
    retry_attempts: int = 3
    retry_delay: float = 1.0
    paper_trading: bool = False  # Set to True to enable paper trading mode