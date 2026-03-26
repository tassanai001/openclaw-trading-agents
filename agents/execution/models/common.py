"""
Common enums and base types for exchange adapters
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class OrderSide(Enum):
    """Order side"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order type"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class ExchangeCredentials:
    """Exchange credentials"""
    api_key: str
    api_secret: str
    testnet: bool = True
    demo_mode: bool = False
    endpoint: Optional[str] = None
