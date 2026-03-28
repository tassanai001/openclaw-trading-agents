"""
Execution Agent for placing orders on Hyperliquid
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time
import sys
import os

# Add the project root to sys.path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.paper_trading_config import PaperTradingConfig

from .hyperliquid_api import HyperliquidAPI, PriceFetcher
from .config import ExecutionConfig
from .slippage_validator import SlippageValidator
from .liquidity_checker import LiquidityChecker
from .binance_price_fetcher import BinancePriceFetcher


class OrderType:
    """Order types supported by the execution agent"""
    BUY = "B"
    SELL = "S"
    SHORT = "SHORT"  # Short sell (borrow and sell)
    COVER = "COVER"  # Cover short (buy back)


@dataclass
class Position:
    """Represents a trading position"""
    asset: str
    size: float  # Positive for long, negative for short
    avg_entry_price: float
    entry_time: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


@dataclass
class OrderResult:
    """Result of an order execution"""
    success: bool
    order_id: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    is_paper_trade: bool = False


class ExecutionAgent:
    """Agent responsible for executing trades on Hyperliquid"""
    
    # Decision thresholds
    LONG_THRESHOLD = 0.2
    SHORT_THRESHOLD = -0.2
    
    def __init__(self, config: ExecutionConfig, paper_trading_config: Optional[PaperTradingConfig] = None):
        self.config = config
        self.paper_trading_config = paper_trading_config or PaperTradingConfig()
        
        # Determine if paper trading is enabled based on config
        self.paper_trading_enabled = config.paper_trading or self.paper_trading_config.enabled
        
        # Initialize price fetcher for current prices
        self.price_fetcher = PriceFetcher(is_testnet=config.is_testnet if not config.paper_trading else True)
        
        # Initialize paper trading state if enabled
        if self.paper_trading_enabled:
            self.paper_balance = self.paper_trading_config.initial_balance
            self.paper_positions: Dict[str, Position] = {}
            self.paper_order_counter = 0
            self.logger = logging.getLogger(f"{__name__}.paper")
            
            # Setup paper trading logger
            if self.paper_trading_config.trade_log_file:
                handler = logging.FileHandler(self.paper_trading_config.trade_log_file)
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
        else:
            self.api = HyperliquidAPI(
                api_key=config.api_key or "",
                secret=config.secret or "",
                is_testnet=config.is_testnet,
                mock_mode=config.mock_mode
            )
            self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize the execution agent"""
        self.logger.info("Initializing Execution Agent")
        # Perform any necessary initialization here
        if self.paper_trading_enabled:
            self.logger.info(f"Paper trading initialized with balance: ${self.paper_balance:.2f}")
        pass
    
    def _calculate_paper_order_price(self, price: Optional[float], side: str, size: float, order_type: str) -> float:
        """Calculate order price considering slippage and fees for paper trading"""
        if price is None:
            simulated_price = asyncio.run(self._get_realistic_price("BTC"))
        else:
            simulated_price = price
            
        # Apply slippage based on order size and direction
        slippage_factor = 1.0
        if self.paper_trading_config.simulate_price_impact:
            slippage_amount = (abs(size) / 1000.0) * (self.paper_trading_config.slippage_percent / 100.0)
            if side == "B":  # Buy order - higher price due to slippage
                slippage_factor = 1 + slippage_amount
            elif side == "S":  # Sell order - lower price due to slippage
                slippage_factor = 1 - slippage_amount
        
        return simulated_price * slippage_factor
    
    def _save_paper_trade_to_db(self, asset: str, side: str, size: float, price: float, fees: float):
        """Save paper trade to database"""
        try:
            import sqlite3
            from datetime import datetime
            conn = sqlite3.connect('trading.db')
            cursor = conn.cursor()
            order_id = f"PAPER_{int(time.time())}_{asset}"
            cursor.execute("""
                INSERT INTO trades (symbol, quantity, price, side, timestamp, order_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (asset, size, price, 'BUY' if side == 'B' else 'SELL', datetime.now().isoformat(), order_id))
            conn.commit()
            conn.close()
            self.logger.info(f"Paper trade saved to DB: {side} {size} {asset} @ {price}")
        except Exception as e:
            self.logger.error(f"Failed to save paper trade to DB: {e}")
    
    def _save_position_to_db(self, asset: str, size: float, avg_price: float, current_price: float):
        """Save/update position to database"""
        try:
            import sqlite3
            from datetime import datetime
            
            conn = sqlite3.connect('trading.db')
            cursor = conn.cursor()
            
            # Calculate unrealized P&L
            if size != 0:
                unrealized_pnl = (current_price - avg_price) * size
            else:
                unrealized_pnl = 0.0
            
            # Check if position exists
            cursor.execute("SELECT id FROM positions WHERE symbol = ?", (asset,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing position
                cursor.execute("""
                    UPDATE positions 
                    SET quantity = ?, avg_price = ?, current_price = ?, unrealized_pnl = ?, timestamp = ?
                    WHERE symbol = ?
                """, (size, avg_price, current_price, unrealized_pnl, datetime.now().isoformat(), asset))
            else:
                # Insert new position (only if size != 0)
                if size != 0:
                    cursor.execute("""
                        INSERT INTO positions (symbol, quantity, avg_price, current_price, unrealized_pnl, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (asset, size, avg_price, current_price, unrealized_pnl, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            if size != 0:
                self.logger.info(f"Position saved to DB: {asset} {size} @ ${avg_price:.2f} | P&L: ${unrealized_pnl:.2f}")
            else:
                self.logger.info(f"Position closed: {asset}")
                
        except Exception as e:
            self.logger.error(f"Failed to save position to DB: {e}")
    
    def _update_paper_position(self, asset: str, side: str, size: float, price: float) -> Dict[str, Any]:
        """Update paper trading position"""
        current_size = 0.0
        avg_price = 0.0
        entry_time = time.time()
        
        if asset in self.paper_positions:
            pos = self.paper_positions[asset]
            current_size = pos.size
            avg_price = pos.avg_entry_price
            entry_time = pos.entry_time
        
        # Calculate new position size
        order_size = size if side == "B" else -size
        new_size = current_size + order_size
        
        # Calculate average entry price
        if new_size == 0:
            # Completely closed position - reset
            new_avg_price = 0.0
            entry_time = time.time()
        elif (current_size > 0 and new_size > 0) or (current_size < 0 and new_size < 0):
            # Same direction trade - adjust average price
            total_value = (current_size * avg_price) + (order_size * price)
            new_avg_price = abs(total_value / new_size)
        elif abs(new_size) < abs(current_size):
            # Reducing position - calculate realized P&L
            closing_size = abs(current_size) - abs(new_size)
            realized_pnl = closing_size * (price - avg_price) if current_size > 0 else closing_size * (avg_price - price)
            
            # Keep the same average price since we're just reducing position
            new_avg_price = avg_price
        else:
            # Reversing position - realize pnl on old position, then enter new
            realized_pnl = abs(current_size) * (price - avg_price) if current_size > 0 else abs(current_size) * (avg_price - price)
            # New position has its own entry price
            new_avg_price = price
            entry_time = time.time()
        
        # Determine realized P&L value
        realized_pnl_value = locals().get('realized_pnl', 0.0)
        
        # Create/update position
        position = Position(
            asset=asset,
            size=new_size,
            avg_entry_price=new_avg_price,
            entry_time=entry_time,
            unrealized_pnl=0.0,  # Will be updated when market prices change
            realized_pnl=realized_pnl_value
        )
        
        self.paper_positions[asset] = position
        
        # Save position to database
        self._save_position_to_db(asset, new_size, new_avg_price, price)
        
        return {
            "position": position,
            "executed_price": price,
            "fees": abs(order_size * price * (self.paper_trading_config.fee_percent / 100.0)),
            "realized_pnl": realized_pnl_value
        }
    
    def _validate_paper_order(self, asset: str, side: str, size: float, price: Optional[float]) -> tuple[bool, str]:
        """Validate paper trading order parameters"""
        # Calculate cost first (need this for min order check)
        if price is None:
            price = asyncio.run(self._get_realistic_price(asset))
        
        estimated_cost = size * price
        
        # Check minimum order size (in USD)
        if estimated_cost < self.paper_trading_config.min_order_size:
            return False, f"Order value ${estimated_cost:.2f} is below minimum of ${self.paper_trading_config.min_order_size:.2f}"
        
        # Check maximum position size
        if estimated_cost > self.paper_balance * self.paper_trading_config.max_position_size:
            return False, f"Position size ${estimated_cost:.2f} would exceed maximum allowed ({self.paper_trading_config.max_position_size * 100}% of ${self.paper_balance:.2f})"
        
        return True, ""
    
    async def place_order(self, 
                          asset: str, 
                          side: str,  # "B" for buy, "S" for sell
                          leverage: int,
                          order_type: str,  # "limit" or "market"
                          price: Optional[float] = None,
                          size: float = 0.0,
                          reduce_only: bool = False) -> OrderResult:
        """
        Place an order - either live or paper trading
        """
        try:
            if self.paper_trading_enabled:
                # Handle paper trading order
                return await self._place_paper_order(asset, side, leverage, order_type, price, size, reduce_only)
            else:
                # Handle live trading order using new SDK
                is_buy = side.upper() in ["B", "BUY"]
                order_data = {
                    "asset": asset,
                    "is_buy": is_buy,
                    "size": size,
                    "price": price,
                    "order_type": order_type.lower(),
                    "reduce_only": reduce_only
                }
                
                self.logger.info(f"Placing {order_type} order: {'BUY' if is_buy else 'SELL'} {size} {asset} @ {price if price else 'MARKET'}")
                
                response = await self.api.place_order(order_data)
                
                if response.get("status") == "success":
                    order_result = OrderResult(
                        success=True,
                        order_id=response.get("order_id"),
                        raw_response=response
                    )
                    self.logger.info(f"Order placed successfully: {order_result.order_id}")
                else:
                    order_result = OrderResult(
                        success=False,
                        error=response.get("error", "Unknown error"),
                        raw_response=response
                    )
                    self.logger.error(f"Order failed: {order_result.error}")
                
                return order_result
                
        except Exception as e:
            self.logger.error(f"Error placing order: {str(e)}")
            return OrderResult(success=False, error=str(e))
    
    async def _place_paper_order(self, 
                                asset: str, 
                                side: str, 
                                leverage: int,
                                order_type: str, 
                                price: Optional[float],
                                size: float,
                                reduce_only: bool = False) -> OrderResult:
        """Handle paper trading order execution"""
        try:
            # Validate order parameters
            is_valid, error_msg = self._validate_paper_order(asset, side, size, price)
            if not is_valid:
                return OrderResult(success=False, error=str(error_msg), is_paper_trade=True)
            
            # Calculate execution price with slippage
            execution_price = self._calculate_paper_order_price(price, side, size, order_type)
            
            # Update position
            result = self._update_paper_position(asset, side, size, execution_price)
            position = result["position"]
            fees = result["fees"]
            
            # Update balance based on trade
            # For simplicity, we'll just track P&L separately rather than adjusting balance on each trade
            # In a real implementation, you'd need to track available margin, etc.
            
            # Save trade to database
            self._save_paper_trade_to_db(asset, side, size, execution_price, fees)
            
            # Generate a paper order ID
            self.paper_order_counter += 1
            order_id = f"PAPER_{int(time.time())}_{self.paper_order_counter}"
            
            # Log the paper trade
            self.logger.info(f"Paper trade executed: {side} {size} {asset} @ {execution_price:.2f} | Fees: ${fees:.2f}")
            self.logger.info(f"Position: Size={position.size:.4f}, AvgPrice=${position.avg_entry_price:.2f}, Realized P&L=${position.realized_pnl:.2f}")
            
            # Create paper order result
            paper_response = {
                "order_id": order_id,
                "status": "filled",
                "executed_price": execution_price,
                "executed_size": size,
                "side": side,
                "asset": asset,
                "fees": fees,
                "timestamp": time.time(),
                "is_paper_trade": True
            }
            
            order_result = OrderResult(
                success=True,
                order_id=order_id,
                raw_response=paper_response,
                is_paper_trade=True
            )
            
            return order_result
            
        except Exception as e:
            self.logger.error(f"Error placing paper order: {str(e)}")
            return OrderResult(success=False, error=str(e), is_paper_trade=True)
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID"""
        try:
            if self.paper_trading_enabled:
                # In paper trading, orders are typically filled instantly, so there's nothing to cancel
                # But we'll return True to simulate successful cancellation for non-existent orders
                self.logger.info(f"Paper trading: Cancellation attempted for order {order_id} (simulated)")
                return True
            else:
                response = await self.api.cancel_order(order_id)
                cancelled = response.get("cancelled", False)
                self.logger.info(f"Order {order_id} cancellation status: {cancelled}")
                return cancelled
        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {str(e)}")
            return False
    
    async def get_open_orders(self, asset: Optional[str] = None) -> Dict[str, Any]:
        """Get open orders"""
        try:
            if self.paper_trading_enabled:
                # In paper trading, we assume all orders are filled immediately, so no open orders
                result = {"open_orders": [], "paper_trading": True}
                if asset:
                    result["asset"] = asset
                return result
            else:
                response = await self.api.get_open_orders(asset)
                return response
        except Exception as e:
            self.logger.error(f"Error getting open orders: {str(e)}")
            return {"open_orders": [], "error": str(e)}
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            if self.paper_trading_enabled:
                # Return paper trading account info
                total_realized_pnl = sum(pos.realized_pnl for pos in self.paper_positions.values())
                
            total_unrealized_pnl = 0.0
            for pos in self.paper_positions.values():
                if pos.size != 0:
                    current_price = asyncio.run(self._get_realistic_price(pos.asset))
                    pos.unrealized_pnl = pos.size * (current_price - pos.avg_entry_price)
                    total_unrealized_pnl += pos.unrealized_pnl
                
                total_equity = self.paper_balance + total_realized_pnl + total_unrealized_pnl
                
                return {
                    "account_value": total_equity,
                    "balance": self.paper_balance,
                    "total_realized_pnl": total_realized_pnl,
                    "total_unrealized_pnl": total_unrealized_pnl,
                    "equity": total_equity,
                    "positions": [{k: v for k, v in pos.__dict__.items()} for pos in self.paper_positions.values()],
                    "paper_trading": True
                }
            else:
                response = await self.api.get_account_info()
                return response
        except Exception as e:
            self.logger.error(f"Error getting account info: {str(e)}")
            return {"error": str(e)}
    
    
    async def execute_order(self, signal: dict) -> OrderResult:
        """
        Execute an order based on a trading signal
        
        Args:
            signal: Trading signal dict with keys: asset, side, size, price, etc.
            
        Returns:
            OrderResult: Result of the order execution
        """
        asset = signal.get('asset', 'BTC')
        side = signal.get('side', 'B')
        size = signal.get('size', 0.01)
        price = signal.get('price')
        order_type = signal.get('order_type', 'market')
        leverage = signal.get('leverage', 1)
        order_action = signal.get('order_action', None)
        
        # Normalize side for SHORT and COVER orders
        normalized_side = side
        if side == OrderType.SHORT:
            normalized_side = "S"  # Short sells
        elif side == OrderType.COVER:
            normalized_side = "B"  # Covering a short means buying
        
        self.logger.info(f"Executing order: {side} {size} {asset} @ {price or 'MARKET'} (action: {order_action or 'none'})")
        
        symbol = asset if "USDT" in asset.upper() else f"{asset}USDT"
        validation_side = "buy" if normalized_side.upper() in ["B", "BUY"] else "sell"
        
        if not await self.validate_slippage(symbol, validation_side, size, price):
            return OrderResult(success=False, error="Slippage validation failed", is_paper_trade=self.paper_trading_enabled)
        
        if not await self.check_liquidity(symbol, validation_side, size):
            return OrderResult(success=False, error="Insufficient liquidity", is_paper_trade=self.paper_trading_enabled)
        
        # Place the order with normalized side
        return await self.place_order(asset, normalized_side, leverage, order_type, price, size)
    
    def validate_slippage(self, pair: str) -> bool:
        """
        Validate that slippage is within acceptable limits
        
        Args:
            pair: Trading pair (e.g., 'BTC-PERP')
            
        Returns:
            bool: True if slippage is acceptable
        """
        # Mock implementation - in production would check real slippage data
        max_slippage = self.config.max_slippage if hasattr(self.config, 'max_slippage') else 0.5
        current_slippage = 0.1  # Mock value
        
        is_valid = current_slippage <= max_slippage
        self.logger.debug(f"Slippage validation for {pair}: {current_slippage}% <= {max_slippage}% = {is_valid}")
        return is_valid
    
    def check_liquidity(self, pair: str, size: float) -> bool:
        """
        Check if there's sufficient liquidity for the order
        
        Args:
            pair: Trading pair (e.g., 'BTC-PERP')
            size: Order size
            
        Returns:
            bool: True if liquidity is sufficient
        """
        # Mock implementation - in production would check order book depth
        min_liquidity = self.config.min_liquidity if hasattr(self.config, 'min_liquidity') else 10000
        available_liquidity = 100000  # Mock value
        
        is_sufficient = available_liquidity >= (size * 50000)  # Assuming ~50k price
        self.logger.debug(f"Liquidity check for {pair}: {available_liquidity} >= {size * 50000} = {is_sufficient}")
        return is_sufficient
    
    async def get_current_price(self, asset: str) -> float:
        """Get current market price for an asset"""
        price = await self.price_fetcher.get_price(asset)
        if price and price > 0:
            return price
        
        if asset in self.paper_positions:
            return self.paper_positions[asset].avg_entry_price
        
        return await self._get_realistic_price(asset)
    
    def signal_to_order(self, signal: float, current_position: Optional[Position] = None) -> Dict[str, Any]:
        """
        Convert signal to order parameters based on decision matrix.
        
        Decision matrix:
        - signal > 0.2: LONG (buy/close short)
        - -0.2 <= signal <= 0.2: HOLD (no action)
        - signal < -0.2: SHORT (sell/close long)
        
        Args:
            signal: Combined signal from scanner and sentiment (-1.0 to 1.0)
            current_position: Current position for the asset if any
            
        Returns:
            Dict with order parameters: action, side, size, etc.
        """
        if signal > self.LONG_THRESHOLD:
            if current_position and current_position.size < 0:
                return {
                    "action": "COVER_SHORT",
                    "side": OrderType.COVER,
                    "size": abs(current_position.size),
                    "reason": "Signal positive, closing short position"
                }
            return {
                "action": "LONG",
                "side": OrderType.BUY,
                "size": 0.01,
                "reason": "Signal > LONG_THRESHOLD, entering long"
            }
        
        elif signal < self.SHORT_THRESHOLD:
            if current_position and current_position.size > 0:
                return {
                    "action": "CLOSE_LONG",
                    "side": OrderType.SELL,
                    "size": abs(current_position.size),
                    "reason": "Signal negative, closing long position"
                }
            return {
                "action": "SHORT",
                "side": OrderType.SHORT,
                "size": 0.01,
                "reason": "Signal < SHORT_THRESHOLD, entering short"
            }
        
        else:
            action = "HOLD"
            if current_position:
                if current_position.size > 0:
                    action = "HOLD_LONG"
                elif current_position.size < 0:
                    action = "HOLD_SHORT"
            
            return {
                "action": action,
                "side": "HOLD",
                "size": 0,
                "reason": f"Signal {signal} within HOLD range (-0.2 to 0.2)"
            }
    
    async def execute_from_signal(self, asset: str, signal: float) -> OrderResult:
        """
        Execute a trade based on a combined signal.
        
        Args:
            asset: Trading pair (e.g., "BTC")
            signal: Combined signal value (-1.0 to 1.0)
            
        Returns:
            OrderResult: Result of the order execution
        """
        current_position = self.paper_positions.get(asset) if self.paper_trading_enabled else None
        
        order_params = self.signal_to_order(signal, current_position)
        
        self.logger.info(f"Signal {signal:.3f} -> Order: {order_params['action']} ({order_params['reason']})")
        
        if order_params["action"] == "HOLD":
            return OrderResult(
                success=True,
                error="HOLD - signal within neutral range",
                is_paper_trade=self.paper_trading_enabled
            )
        
        side = order_params["side"]
        size = order_params["size"]
        
        current_price = await self.get_current_price(asset)
        
        result = await self.execute_order({
            "asset": asset,
            "side": side if isinstance(side, str) else "B",
            "size": size,
            "price": current_price,
            "order_type": "market",
            "leverage": 1,
            "order_action": order_params["action"]
        })
        
        return result

    async def validate_slippage(self, symbol: str, side: str, size: float, price: Optional[float] = None) -> bool:
        """
        Validate that slippage is within acceptable limits using real order book data
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            side: "buy" or "sell"
            size: Order size in base asset
            price: Current market price (optional)
            
        Returns:
            bool: True if slippage is acceptable
        """
        use_real_validation = getattr(self.config, 'use_real_validation', True)
        max_slippage = getattr(self.config, 'max_slippage_percent', 0.5)
        
        if not use_real_validation:
            current_slippage = 0.1
            is_valid = current_slippage <= max_slippage
            self.logger.debug(f"Mock slippage validation for {symbol}: {current_slippage}% <= {max_slippage}% = {is_valid}")
            return is_valid
        
        try:
            validator = SlippageValidator("hyperliquid", self.config)
            current_slippage = await validator.get_slippage(symbol, side, size, price)
            is_valid = current_slippage <= max_slippage
            self.logger.debug(f"Real slippage validation for {symbol}: {current_slippage:.3f}% <= {max_slippage}% = {is_valid}")
            return is_valid
        except Exception as e:
            self.logger.error(f"Slippage validation failed for {symbol}: {e}")
            return False
    
    async def check_liquidity(self, symbol: str, side: str, size: float) -> bool:
        """
        Check if there's sufficient liquidity for the order using real order book data
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            side: "buy" or "sell"
            size: Required order size
            
        Returns:
            bool: True if liquidity is sufficient
        """
        use_real_validation = getattr(self.config, 'use_real_validation', True)
        min_liquidity_usd = getattr(self.config, 'min_liquidity_usd', 50000.0)
        
        if not use_real_validation:
            available_liquidity = 100000
            is_sufficient = available_liquidity >= (size * 50000)
            self.logger.debug(f"Mock liquidity check for {symbol}: {available_liquidity} >= {size * 50000} = {is_sufficient}")
            return is_sufficient
        
        try:
            checker = LiquidityChecker("hyperliquid", self.config)
            is_sufficient, available_size = await checker.check_liquidity(symbol, side, size)
            self.logger.debug(f"Real liquidity check for {symbol}: sufficient={is_sufficient}, available_size={available_size}")
            return is_sufficient
        except Exception as e:
            self.logger.error(f"Liquidity check failed for {symbol}: {e}")
            return False
    
    async def _get_realistic_price(self, asset: str) -> float:
        """Get realistic price from BinancePriceFetcher for paper trading"""
        try:
            fetcher = BinancePriceFetcher(demo_mode=True)
            await fetcher.initialize()
            price = await fetcher.get_price(asset)
            if price and price > 0:
                return price
        except Exception as e:
            self.logger.warning(f"Failed to get realistic price for {asset}: {e}")
        
        return 50000.0
    
    async def close(self):
        """Clean up resources"""
        if hasattr(self, 'price_fetcher'):
            await self.price_fetcher.close()
        
        if not self.paper_trading_enabled and hasattr(self, 'api'):
            await self.api.close()
        else:
            if self.paper_trading_enabled:
                total_realized_pnl = sum(pos.realized_pnl for pos in self.paper_positions.values())
                self.logger.info(f"Paper trading session ended - Total realized P&L: ${total_realized_pnl:.2f}")