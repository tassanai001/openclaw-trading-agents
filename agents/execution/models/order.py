"""
Order data models
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from .common import OrderSide, OrderType, OrderStatus


@dataclass
class Order:
    """Represents a trading order"""
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # GTC, IOC, FOK
    client_order_id: Optional[str] = None


@dataclass
class OrderResult:
    """Result of an order execution"""
    success: bool
    order_id: Optional[str] = None
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    fee: float = 0.0
    fee_currency: str = "USDT"
    status: OrderStatus = OrderStatus.PENDING
    message: str = ""
    raw_response: Optional[dict] = None
    
    @classmethod
    def success_result(cls, order_id: str, filled_qty: float = 0.0, 
                       filled_price: float = 0.0, fee: float = 0.0,
                       raw_response: dict = None):
        """Create a success result"""
        return cls(
            success=True,
            order_id=order_id,
            filled_quantity=filled_qty,
            filled_price=filled_price,
            fee=fee,
            status=OrderStatus.FILLED if filled_qty > 0 else OrderStatus.PENDING,
            raw_response=raw_response
        )
    
    @classmethod
    def error_result(cls, message: str, raw_response: dict = None):
        """Create an error result"""
        return cls(
            success=False,
            message=message,
            status=OrderStatus.REJECTED,
            raw_response=raw_response
        )
