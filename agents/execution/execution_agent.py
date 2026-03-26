"""
Execution Agent using Adapter Pattern

Supports both Binance and Hyperliquid exchanges through a unified interface.
Maintains backward compatibility with the existing orchestrator API.
"""
import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import time

from .adapters.base import ExchangeAdapter
from .adapters.binance import BinanceAdapter
from .adapters.hyperliquid import HyperliquidAdapter
from .models.order import Order, OrderResult
from .models.position import Position, Balance
from .models.common import ExchangeCredentials, OrderSide, OrderType, OrderStatus
from .config import ExecutionConfig
from config.paper_trading_config import PaperTradingConfig


logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Trading signal"""
    asset: str
    side: str  # "B", "S", "BUY", "SELL"
    size: float
    price: Optional[float] = None
    order_type: str = "market"
    leverage: int = 1
    order_action: Optional[str] = None


class ExecutionAgent:
    """
    Execution Agent with Adapter Pattern
    
    Supports:
    - Binance Spot Testnet
    - Hyperliquid Testnet
    - Paper Trading Mode
    """
    
    # Decision thresholds
    LONG_THRESHOLD = 0.2
    SHORT_THRESHOLD = -0.2
    
    def __init__(
        self, 
        exchange: str = "binance",
        config: Optional[ExecutionConfig] = None,
        paper_trading_config: Optional[PaperTradingConfig] = None
    ):
        """
        Initialize Execution Agent
        
        Args:
            exchange: Exchange name ("binance" or "hyperliquid")
            config: Execution configuration
            paper_trading_config: Paper trading configuration
        """
        self.exchange = exchange.lower()
        self.config = config or ExecutionConfig()
        self.paper_trading_config = paper_trading_config or PaperTradingConfig()
        
        # Determine if paper trading is enabled
        self.paper_trading_enabled = self.config.paper_trading or self.paper_trading_config.enabled
        
        # Initialize adapter
        self.adapter: Optional[ExchangeAdapter] = None
        self._load_credentials()
        
        # Paper trading state
        if self.paper_trading_enabled:
            self.paper_balance = self.paper_trading_config.initial_balance
            self.paper_positions: Dict[str, Position] = {}
            self.paper_order_counter = 0
            self.paper_logger = logging.getLogger(f"{__name__}.paper")
            
            # Setup paper trading logger
            if self.paper_trading_config.trade_log_file:
                handler = logging.FileHandler(self.paper_trading_config.trade_log_file)
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.paper_logger.addHandler(handler)
                self.paper_logger.setLevel(logging.INFO)
    
    def _load_credentials(self):
        """Load credentials from environment or config"""
        if self.exchange == "binance":
            self.credentials = ExchangeCredentials(
                api_key=os.getenv("BINANCE_API_KEY", self.config.api_key or ""),
                api_secret=os.getenv("BINANCE_API_SECRET", self.config.secret or ""),
                testnet=os.getenv("BINANCE_TESTNET", "true").lower() == "true",
                demo_mode=os.getenv("BINANCE_DEMO_MODE", "false").lower() == "true",
                endpoint=os.getenv("BINANCE_ENDPOINT")
            )
        elif self.exchange == "hyperliquid":
            self.credentials = ExchangeCredentials(
                api_key=os.getenv("HYPERLIQUID_API_KEY", self.config.api_key or ""),
                api_secret=os.getenv("HYPERLIQUID_API_SECRET", self.config.secret or ""),
                testnet=self.config.is_testnet,
                endpoint=self.config.base_url
            )
        else:
            raise ValueError(f"Unknown exchange: {self.exchange}")
    
    async def initialize(self) -> bool:
        """Initialize the execution agent and adapter"""
        logger.info(f"Initializing Execution Agent for {self.exchange}")
        
        if self.paper_trading_enabled:
            logger.info(f"Paper trading enabled with balance: ${self.paper_balance:.2f}")
            self._initialized = True
            return True
        
        # Create adapter based on exchange selection
        if self.exchange == "binance":
            self.adapter = BinanceAdapter(self.credentials)
        elif self.exchange == "hyperliquid":
            self.adapter = HyperliquidAdapter(self.credentials)
        else:
            logger.error(f"Unsupported exchange: {self.exchange}")
            return False
        
        # Initialize adapter
        success = await self.adapter.initialize()
        self._initialized = success
        return success
    
    async def place_order(
        self,
        asset: str,
        side: str,
        leverage: int,
        order_type: str,
        price: Optional[float] = None,
        size: float = 0.0,
        reduce_only: bool = False
    ) -> OrderResult:
        """
        Place an order - delegates to adapter or paper trading
        
        Args:
            asset: Trading pair (e.g., "BTCUSDT")
            side: "B" for buy, "S" for sell
            leverage: Leverage (not used for spot)
            order_type: "limit" or "market"
            price: Price for limit orders
            size: Order size
            reduce_only: Reduce only flag
            
        Returns:
            OrderResult: Result of the order
        """
        if self.paper_trading_enabled:
            return await self._place_paper_order(asset, side, leverage, order_type, price, size, reduce_only)
        
        if not self.adapter:
            return OrderResult.error_result("Adapter not initialized")
        
        # Convert to adapter Order format
        order_side = OrderSide.BUY if side.upper() in ["B", "BUY"] else OrderSide.SELL
        order_type_enum = OrderType.MARKET if order_type.lower() == "market" else OrderType.LIMIT
        
        # Ensure symbol has USDT suffix
        symbol = asset if "USDT" in asset.upper() else f"{asset}USDT"
        
        order = Order(
            symbol=symbol,
            side=order_side,
            type=order_type_enum,
            quantity=size,
            price=price,
            time_in_force="GTC"
        )
        
        result = await self.adapter.place_order(order)
        
        logger.info(
            f"Order placed: {order_side.value} {size} {symbol} @ {price or 'MARKET'} | "
            f"Success: {result.success}, Order ID: {result.order_id}"
        )
        
        return result
    
    async def _place_paper_order(
        self,
        asset: str,
        side: str,
        leverage: int,
        order_type: str,
        price: Optional[float],
        size: float,
        reduce_only: bool = False
    ) -> OrderResult:
        """Handle paper trading order"""
        try:
            # Simple paper trading implementation
            execution_price = price or 50000.0  # Placeholder
            order_id = f"PAPER_{int(time.time())}_{self.paper_order_counter}"
            self.paper_order_counter += 1
            
            self.paper_logger.info(
                f"Paper order: {side} {size} {asset} @ {execution_price:.2f}"
            )
            
            return OrderResult.success_result(
                order_id=order_id,
                filled_qty=size,
                filled_price=execution_price,
                fee=execution_price * size * 0.001,  # 0.1% fee
                raw_response={"is_paper_trade": True}
            )
        except Exception as e:
            logger.error(f"Paper order failed: {e}")
            return OrderResult.error_result(str(e))
    
    async def cancel_order(self, order_id: str, symbol: str = "BTCUSDT") -> bool:
        """Cancel an order"""
        if self.paper_trading_enabled:
            logger.info(f"Paper trading: Cancel order {order_id} (simulated)")
            return True
        
        if not self.adapter:
            return False
        
        return await self.adapter.cancel_order(symbol, order_id)
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders"""
        if self.paper_trading_enabled:
            return []  # Paper trades are instant
        
        if not self.adapter:
            return []
        
        return await self.adapter.get_open_orders(symbol)
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a symbol"""
        if not self.adapter:
            return None
        
        return await self.adapter.get_position(symbol)
    
    async def get_positions(self) -> List[Position]:
        """Get all positions"""
        if not self.adapter:
            return []
        
        return await self.adapter.get_positions()
    
    async def get_balance(self) -> Balance:
        """Get account balance"""
        if self.paper_trading_enabled:
            return Balance(
                total_balance=self.paper_balance,
                available_balance=self.paper_balance,
                locked_balance=0,
                currency="USDT"
            )
        
        if not self.adapter:
            return Balance(total_balance=0, available_balance=0, locked_balance=0)
        
        return await self.adapter.get_balance()
    
    async def get_ticker_price(self, symbol: str) -> float:
        """Get current market price"""
        if not self.adapter:
            return 0.0
        
        return await self.adapter.get_ticker_price(symbol)
    
    async def execute_signal(self, signal: dict) -> OrderResult:
        """
        Execute a trading signal
        
        Args:
            signal: Signal dict with keys: asset, side, size, price, etc.
            
        Returns:
            OrderResult: Result of execution
        """
        asset = signal.get("asset", "BTC")
        side = signal.get("side", "B")
        size = signal.get("size", 0.001)
        price = signal.get("price")
        order_type = signal.get("order_type", "market")
        leverage = signal.get("leverage", 1)
        
        logger.info(f"Executing signal: {side} {size} {asset} @ {price or 'MARKET'}")
        
        return await self.place_order(asset, side, leverage, order_type, price, size)
    
    async def execute_from_signal(self, asset: str, signal: float) -> OrderResult:
        """
        Execute from a numeric signal
        
        Args:
            asset: Asset name
            signal: Signal value (-1.0 to 1.0)
            
        Returns:
            OrderResult: Result of execution
        """
        if signal > self.LONG_THRESHOLD:
            side = "B"
            action = "LONG"
        elif signal < self.SHORT_THRESHOLD:
            side = "S"
            action = "SHORT"
        else:
            return OrderResult(
                success=True,
                message=f"HOLD - signal {signal} within neutral range"
            )
        
        current_price = await self.get_ticker_price(f"{asset}USDT")
        
        return await self.execute_order({
            "asset": asset,
            "side": side,
            "size": 0.001,
            "price": current_price,
            "order_type": "market",
            "leverage": 1,
            "order_action": action
        })
    
    async def execute_order(self, signal: dict) -> OrderResult:
        """Execute order from signal dict"""
        return await self.execute_signal(signal)
    
    def signal_to_order(self, signal: float, current_position: Optional[Position] = None) -> Dict[str, Any]:
        """
        Convert signal to order parameters
        
        Decision matrix:
        - signal > 0.2: LONG
        - signal < -0.2: SHORT
        - otherwise: HOLD
        """
        if signal > self.LONG_THRESHOLD:
            return {
                "action": "LONG",
                "side": "B",
                "size": 0.01,
                "reason": "Signal > LONG_THRESHOLD"
            }
        elif signal < self.SHORT_THRESHOLD:
            return {
                "action": "SHORT",
                "side": "S",
                "size": 0.01,
                "reason": "Signal < SHORT_THRESHOLD"
            }
        else:
            return {
                "action": "HOLD",
                "side": "HOLD",
                "size": 0,
                "reason": f"Signal {signal} in neutral range"
            }
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        if self.paper_trading_enabled:
            return {
                "account_value": self.paper_balance,
                "balance": self.paper_balance,
                "paper_trading": True
            }
        
        balance = await self.get_balance()
        positions = await self.get_positions()
        
        return {
            "account_value": balance.total_balance,
            "balance": balance.available_balance,
            "positions": positions,
            "paper_trading": False
        }
    
    async def close(self):
        """Clean up resources"""
        if self.adapter:
            await self.adapter.close()
        logger.info("Execution Agent closed")
