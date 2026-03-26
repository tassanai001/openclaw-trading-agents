"""
Position and balance data models
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    quantity: float
    avg_entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    side: str = "LONG"  # LONG, SHORT, NONE
    
    def update_price(self, price: float):
        """Update current price and recalculate unrealized P&L"""
        self.current_price = price
        if self.side == "LONG":
            self.unrealized_pnl = (price - self.avg_entry_price) * self.quantity
        elif self.side == "SHORT":
            self.unrealized_pnl = (self.avg_entry_price - price) * self.quantity
    
    @property
    def market_value(self) -> float:
        """Get market value of position"""
        return self.current_price * abs(self.quantity)


@dataclass
class Balance:
    """Represents account balance"""
    total_balance: float  # In USDT
    available_balance: float
    locked_balance: float
    currency: str = "USDT"
    balances: Dict[str, dict] = field(default_factory=dict)  # { "BTC": {"free": 0.5, "locked": 0.1, "total": 0.6} }
    
    @classmethod
    def from_dict(cls, data: dict, currency: str = "USDT"):
        """Create Balance from dict"""
        return cls(
            total_balance=data.get("total", 0.0),
            available_balance=data.get("available", 0.0),
            locked_balance=data.get("locked", 0.0),
            currency=currency,
            balances=data.get("balances", {})
        )
