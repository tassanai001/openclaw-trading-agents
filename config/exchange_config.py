"""
Exchange Configuration
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExchangeConfig:
    """Configuration for exchange selection"""
    name: str
    testnet: bool
    api_key: str
    api_secret: str
    endpoint: Optional[str] = None
    
    @classmethod
    def from_env(cls, exchange: str = "binance"):
        """Create ExchangeConfig from environment variables"""
        if exchange.lower() == "binance":
            return cls(
                name="binance",
                testnet=os.getenv("BINANCE_TESTNET", "true").lower() == "true",
                api_key=os.getenv("BINANCE_API_KEY", ""),
                api_secret=os.getenv("BINANCE_API_SECRET", ""),
                endpoint=os.getenv("BINANCE_ENDPOINT")
            )
        elif exchange.lower() == "hyperliquid":
            return cls(
                name="hyperliquid",
                testnet=True,
                api_key=os.getenv("HYPERLIQUID_API_KEY", ""),
                api_secret=os.getenv("HYPERLIQUID_API_SECRET", ""),
                endpoint=os.getenv("HYPERLIQUID_ENDPOINT", "https://api.hyperliquid-testnet.xyz")
            )
        else:
            raise ValueError(f"Unsupported exchange: {exchange}")


# Global config - reads from environment
ACTIVE_EXCHANGE = os.getenv("ACTIVE_EXCHANGE", "binance")
config = ExchangeConfig.from_env(ACTIVE_EXCHANGE)
