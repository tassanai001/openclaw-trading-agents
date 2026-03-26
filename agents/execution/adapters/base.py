"""
Abstract base class for exchange adapters
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.order import Order, OrderResult
from ..models.position import Position, Balance
from ..models.common import ExchangeCredentials


class ExchangeAdapter(ABC):
    """
    Abstract Base Class for Exchange Adapter
    Every adapter must implement these methods
    """
    
    def __init__(self, credentials: ExchangeCredentials):
        self.credentials = credentials
        self.testnet = credentials.testnet
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize connection to exchange"""
        pass
    
    @abstractmethod
    async def place_order(self, order: Order) -> OrderResult:
        """Place an order and return result"""
        pass
    
    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get list of open orders"""
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for a symbol"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all positions"""
        pass
    
    @abstractmethod
    async def get_balance(self) -> Balance:
        """Get account balance"""
        pass
    
    @abstractmethod
    async def get_ticker_price(self, symbol: str) -> float:
        """Get current market price for a symbol"""
        pass
    
    @abstractmethod
    def get_symbol_info(self, symbol: str) -> dict:
        """Get symbol info (precision, min qty, etc.)"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Exchange name"""
        pass
