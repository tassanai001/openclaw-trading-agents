"""
Hyperliquid Testnet Adapter

Wraps the existing Hyperliquid API logic into the adapter pattern
"""
import asyncio
import logging
from typing import List, Optional
from ..adapters.base import ExchangeAdapter
from ..models.order import Order, OrderResult
from ..models.position import Position, Balance
from ..models.common import ExchangeCredentials, OrderSide, OrderType, OrderStatus

logger = logging.getLogger(__name__)


class HyperliquidAdapter(ExchangeAdapter):
    """
    Hyperliquid Testnet Adapter
    
    Wraps existing HyperliquidAPI logic into the adapter pattern
    """
    
    def __init__(self, credentials: ExchangeCredentials):
        super().__init__(credentials)
        self.api = None
        self._price_fetcher = None
    
    @property
    def name(self) -> str:
        return "Hyperliquid"
    
    async def initialize(self) -> bool:
        """Initialize Hyperliquid client"""
        try:
            # Import here to avoid circular imports
            from ..hyperliquid_api import HyperliquidAPI, PriceFetcher
            
            self.api = HyperliquidAPI(
                api_key=self.credentials.api_key,
                secret=self.credentials.api_secret,
                is_testnet=self.testnet,
                mock_mode=False
            )
            self._price_fetcher = PriceFetcher(is_testnet=self.testnet)
            self._initialized = True
            logger.info(f"✅ Hyperliquid Adapter initialized (testnet={self.testnet})")
            return True
        except Exception as e:
            logger.error(f"❌ Hyperliquid Adapter initialization failed: {e}")
            return False
    
    async def place_order(self, order: Order) -> OrderResult:
        """Place order on Hyperliquid"""
        if not self._initialized:
            return OrderResult.error_result("Adapter not initialized")
        
        try:
            # Convert Order to Hyperliquid format
            is_buy = order.side == OrderSide.BUY
            order_type = "market" if order.type == OrderType.MARKET else "limit"
            
            order_data = {
                "asset": order.symbol.replace("USDT", ""),  # Hyperliquid uses "BTC" not "BTCUSDT"
                "is_buy": is_buy,
                "size": order.quantity,
                "price": order.price,
                "order_type": order_type,
                "reduce_only": False
            }
            
            response = await self.api.place_order(order_data)
            
            if response.get("status") == "success":
                order_id = response.get("order_id")
                fills = response.get("fills", [])
                
                # Calculate filled quantity and price from fills
                filled_qty = sum(float(f.get("sz", 0)) for f in fills) if fills else order.quantity
                filled_price = sum(float(f.get("px", 0)) for f in fills) / len(fills) if fills else (order.price or 0)
                
                # Estimate fee (Hyperliquid: ~0.035% for taker)
                fee = filled_qty * filled_price * 0.00035
                
                return OrderResult.success_result(
                    order_id=str(order_id),
                    filled_qty=filled_qty,
                    filled_price=filled_price,
                    fee=fee,
                    raw_response=response
                )
            else:
                return OrderResult.error_result(
                    response.get("error", "Unknown error"),
                    raw_response=response
                )
            
        except Exception as e:
            return OrderResult.error_result(f"Hyperliquid order failed: {str(e)}")
    
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel order"""
        try:
            asset = symbol.replace("USDT", "")
            response = await self.api.cancel_order(order_id, asset)
            return response.get("cancelled", False)
        except Exception as e:
            logger.error(f"Cancel order failed: {e}")
            return False
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders"""
        try:
            asset = symbol.replace("USDT", "") if symbol else None
            response = await self.api.get_open_orders(asset)
            
            orders = []
            for o in response.get("open_orders", []):
                orders.append(Order(
                    symbol=f"{o.get('coin')}USDT",
                    side=OrderSide.BUY if o.get("side") == "A" else OrderSide.SELL,
                    type=OrderType.LIMIT,
                    quantity=float(o.get("sz", 0)),
                    price=float(o.get("px", 0)),
                    client_order_id=o.get("oid")
                ))
            return orders
        except Exception as e:
            logger.error(f"Get open orders failed: {e}")
            return []
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol"""
        try:
            asset = symbol.replace("USDT", "")
            response = await self.api.get_positions()
            
            positions = response.get("positions", [])
            for pos in positions:
                if pos.get("coin") == asset:
                    szi = float(pos.get("szi", 0))
                    entry_px = float(pos.get("entryPx", 0))
                    
                    # Get current price
                    current_price = await self.get_ticker_price(symbol)
                    
                    # Calculate unrealized P&L
                    if szi > 0:
                        unrealized_pnl = (current_price - entry_px) * szi
                        side = "LONG"
                    else:
                        unrealized_pnl = (entry_px - current_price) * abs(szi)
                        side = "SHORT"
                    
                    return Position(
                        symbol=symbol,
                        quantity=abs(szi),
                        avg_entry_price=entry_px,
                        current_price=current_price,
                        unrealized_pnl=unrealized_pnl,
                        side=side
                    )
            
            return None
        except Exception as e:
            logger.error(f"Get position failed: {e}")
            return None
    
    async def get_positions(self) -> List[Position]:
        """Get all positions"""
        positions = []
        try:
            response = await self.api.get_positions()
            
            for pos in response.get("positions", []):
                asset = pos.get("coin")
                symbol = f"{asset}USDT"
                szi = float(pos.get("szi", 0))
                entry_px = float(pos.get("entryPx", 0))
                
                if szi != 0:
                    current_price = await self.get_ticker_price(symbol)
                    
                    if szi > 0:
                        unrealized_pnl = (current_price - entry_px) * szi
                        side = "LONG"
                    else:
                        unrealized_pnl = (entry_px - current_price) * abs(szi)
                        side = "SHORT"
                    
                    positions.append(Position(
                        symbol=symbol,
                        quantity=abs(szi),
                        avg_entry_price=entry_px,
                        current_price=current_price,
                        unrealized_pnl=unrealized_pnl,
                        side=side
                    ))
        except Exception as e:
            logger.error(f"Get positions failed: {e}")
        
        return positions
    
    async def get_balance(self) -> Balance:
        """Get account balance"""
        try:
            response = await self.api.get_account_info()
            
            account_value = response.get("account_value", 0)
            balances_data = response.get("balances", [])
            
            # Parse balances
            balances = {}
            usdt_available = 0
            usdt_locked = 0
            
            for bal in balances_data:
                coin = bal.get("coin", "")
                amount = float(bal.get("amount", 0))
                if coin:
                    balances[coin] = {
                        "free": amount,
                        "locked": 0,  # Hyperliquid doesn't separate free/locked in this response
                        "total": amount
                    }
                    if coin == "USDC":
                        usdt_available = amount
            
            return Balance(
                total_balance=account_value,
                available_balance=usdt_available,
                locked_balance=usdt_locked,
                currency="USDT",
                balances=balances
            )
        except Exception as e:
            logger.error(f"Get balance failed: {e}")
            return Balance(total_balance=0, available_balance=0, locked_balance=0)
    
    async def get_ticker_price(self, symbol: str) -> float:
        """Get current price"""
        try:
            asset = symbol.replace("USDT", "")
            price = await self._price_fetcher.get_price(asset)
            return price if price > 0 else 0.0
        except Exception as e:
            logger.error(f"Get ticker failed: {e}")
            return 0.0
    
    def get_symbol_info(self, symbol: str) -> dict:
        """Get symbol info"""
        # Hyperliquid uses standard precision
        return {
            "base_asset_precision": 8,
            "quote_precision": 8,
            "base_asset_step_size": 0.0001,
            "quote_asset_step_size": 0.1,
            "min_quantity": 0.0001,
            "min_notional": 5.0  # Minimum $5 order
        }
    
    async def close(self):
        """Close client connection"""
        if self.api:
            await self.api.close()
        if self._price_fetcher:
            await self._price_fetcher.close()
