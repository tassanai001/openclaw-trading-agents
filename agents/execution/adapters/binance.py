"""
Binance Spot Adapter

Supports:
- Testnet: https://testnet.binance.vision
- Demo Mode: https://demo-api.binance.com
- Mainnet: https://api.binance.com

API Docs: https://binance-docs.github.io/apidocs/spot/en/

Demo Mode vs Testnet:
- Demo Mode: Real market data, demo balances (https://demo-api.binance.com)
- Testnet: Separate test environment (https://testnet.binance.vision)
"""
import asyncio
from typing import List, Optional
from binance import AsyncClient
from ..adapters.base import ExchangeAdapter
from ..models.order import Order, OrderResult
from ..models.position import Position, Balance
from ..models.common import ExchangeCredentials, OrderSide, OrderType, OrderStatus


class BinanceAdapter(ExchangeAdapter):
    """
    Binance Spot Adapter
    
    Supports Testnet, Demo Mode, and Mainnet
    
    Demo Mode Configuration:
    - Set demo_mode=True in credentials or environment
    - Uses official Binance Demo API (demo-api.binance.com)
    - Requires python-binance >= 1.0.20
    """
    
    TESTNET_URL = "https://testnet.binance.vision"
    DEMO_URL = "https://demo-api.binance.com"
    MAINNET_URL = "https://api.binance.com"
    
    def __init__(self, credentials: ExchangeCredentials):
        super().__init__(credentials)
        self.client: Optional[AsyncClient] = None
        self._symbol_info_cache = {}
        # Check for demo_mode attribute or env var
        self.demo_mode = getattr(credentials, 'demo_mode', False)
    
    @property
    def name(self) -> str:
        return "Binance"
    
    async def initialize(self) -> bool:
        """Initialize Binance client"""
        try:
            if self.demo_mode:
                # Demo Mode: Use demo=True parameter (requires python-binance >= 1.0.20)
                self.client = AsyncClient(
                    api_key=self.credentials.api_key,
                    api_secret=self.credentials.api_secret,
                    demo=True  # This sets the correct endpoint automatically
                )
                print(f"✅ Binance Adapter initialized (DEMO MODE - {self.DEMO_URL})")
            elif self.testnet:
                # Testnet: Use testnet parameter
                self.client = AsyncClient(
                    api_key=self.credentials.api_key,
                    api_secret=self.credentials.api_secret,
                    testnet=True
                )
                print(f"✅ Binance Adapter initialized (TESTNET - {self.TESTNET_URL})")
            else:
                # Mainnet: No special parameters
                self.client = AsyncClient(
                    api_key=self.credentials.api_key,
                    api_secret=self.credentials.api_secret
                )
                print(f"✅ Binance Adapter initialized (MAINNET - {self.MAINNET_URL})")
            
            self._initialized = True
            return True
        except Exception as e:
            print(f"❌ Binance Adapter initialization failed: {e}")
            return False
    
    async def place_order(self, order: Order) -> OrderResult:
        """Place order on Binance"""
        if not self._initialized:
            return OrderResult.error_result("Adapter not initialized")
        
        try:
            # Convert order to Binance format
            params = {
                "symbol": order.symbol.upper(),  # BTCUSDT
                "side": order.side.value,        # BUY/SELL
                "type": order.type.value,        # MARKET/LIMIT
                "quantity": self._format_quantity(order.symbol, order.quantity),
            }
            
            if order.type == OrderType.LIMIT:
                params["price"] = self._format_price(order.symbol, order.price)
                params["timeInForce"] = order.time_in_force
            
            if order.client_order_id:
                params["newClientOrderId"] = order.client_order_id
            
            # Place order
            response = await self.client.create_order(**params)
            
            # Parse response
            filled_qty = float(response.get("executedQty", 0))
            filled_price = float(response.get("price", 0))
            order_id = response.get("orderId")
            status = response.get("status", "NEW")
            
            # Calculate fee (Binance: 0.1% spot, 0.075% with BNB)
            fee = float(response.get("cummulativeQuoteQty", 0)) * 0.001
            
            return OrderResult.success_result(
                order_id=str(order_id),
                filled_qty=filled_qty,
                filled_price=filled_price,
                fee=fee,
                raw_response=response
            )
            
        except Exception as e:
            return OrderResult.error_result(f"Binance order failed: {str(e)}")
    
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel order"""
        try:
            await self.client.cancel_order(
                symbol=symbol.upper(),
                orderId=int(order_id)
            )
            return True
        except Exception as e:
            print(f"Cancel order failed: {e}")
            return False
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders"""
        try:
            if symbol:
                orders = await self.client.get_open_orders(symbol=symbol.upper())
            else:
                orders = await self.client.get_open_orders()
            
            return [self._parse_order(o) for o in orders]
        except Exception as e:
            print(f"Get open orders failed: {e}")
            return []
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol (spot = balance)"""
        try:
            # For spot, position = balance of base asset
            base_asset = symbol.replace("USDT", "")
            account = await self.client.get_account()
            
            for balance in account["balances"]:
                if balance["asset"] == base_asset:
                    qty = float(balance["free"]) + float(balance["locked"])
                    if qty > 0:
                        # Get current price
                        ticker = await self.client.get_symbol_ticker(symbol=symbol)
                        price = float(ticker["price"])
                        return Position(
                            symbol=symbol,
                            quantity=qty,
                            avg_entry_price=price,  # Spot doesn't track avg entry
                            current_price=price,
                            side="LONG"
                        )
            return None
        except Exception as e:
            print(f"Get position failed: {e}")
            return None
    
    async def get_positions(self) -> List[Position]:
        """Get all positions (non-zero balances)"""
        positions = []
        try:
            account = await self.client.get_account()
            
            # Get prices for all symbols
            tickers = await self.client.get_symbol_ticker()
            price_map = {t["symbol"]: float(t["price"]) for t in tickers}
            
            for balance in account["balances"]:
                qty = float(balance["free"]) + float(balance["locked"])
                if qty > 0 and balance["asset"] != "USDT":
                    symbol = f"{balance['asset']}USDT"
                    price = price_map.get(symbol, 0)
                    if price > 0:
                        positions.append(Position(
                            symbol=symbol,
                            quantity=qty,
                            avg_entry_price=price,
                            current_price=price,
                            side="LONG"
                        ))
        except Exception as e:
            print(f"Get positions failed: {e}")
        
        return positions
    
    async def get_balance(self) -> Balance:
        """Get account balance"""
        try:
            account = await self.client.get_account()
            balances = {}
            
            for bal in account["balances"]:
                asset = bal["asset"]
                free = float(bal["free"])
                locked = float(bal["locked"])
                if free > 0 or locked > 0:
                    balances[asset] = {
                        "free": free,
                        "locked": locked,
                        "total": free + locked
                    }
            
            # Calculate total in USDT
            usdt_balance = balances.get("USDT", {"total": 0})
            total = usdt_balance["total"]
            
            # Add value of other assets in USDT
            tickers = await self.client.get_symbol_ticker()
            price_map = {t["symbol"]: float(t["price"]) for t in tickers}
            
            for asset, bal in balances.items():
                if asset != "USDT":
                    symbol = f"{asset}USDT"
                    if symbol in price_map:
                        total += bal["total"] * price_map[symbol]
            
            return Balance(
                total_balance=total,
                available_balance=usdt_balance.get("free", 0),
                locked_balance=usdt_balance.get("locked", 0),
                currency="USDT",
                balances=balances
            )
        except Exception as e:
            print(f"Get balance failed: {e}")
            return Balance(total_balance=0, available_balance=0, locked_balance=0)
    
    async def get_ticker_price(self, symbol: str) -> float:
        """Get current price"""
        try:
            ticker = await self.client.get_symbol_ticker(symbol=symbol.upper())
            return float(ticker["price"])
        except Exception as e:
            print(f"Get ticker failed: {e}")
            return 0.0
    
    def get_symbol_info(self, symbol: str) -> dict:
        """Get symbol precision info"""
        if symbol in self._symbol_info_cache:
            return self._symbol_info_cache[symbol]
        
        # Default precision for most pairs
        info = {
            "base_asset_precision": 8,
            "quote_precision": 8,
            "base_asset_step_size": 0.00001,
            "quote_asset_step_size": 0.01,
            "min_quantity": 0.00001,
            "min_notional": 10.0  # Minimum $10 order
        }
        
        self._symbol_info_cache[symbol] = info
        return info
    
    def _format_quantity(self, symbol: str, quantity: float) -> float:
        """Format quantity according to symbol precision"""
        info = self.get_symbol_info(symbol)
        step = info["base_asset_step_size"]
        return round(quantity / step) * step
    
    def _format_price(self, symbol: str, price: float) -> float:
        """Format price according to symbol precision"""
        info = self.get_symbol_info(symbol)
        step = info["quote_asset_step_size"]
        return round(price / step) * step
    
    def _parse_order(self, data: dict) -> Order:
        """Parse Binance order dict to Order object"""
        return Order(
            symbol=data["symbol"],
            side=OrderSide(data["side"]),
            type=OrderType(data["type"]),
            quantity=float(data["origQty"]),
            price=float(data.get("price", 0)) or None,
            time_in_force=data.get("timeInForce", "GTC"),
            client_order_id=data.get("clientOrderId")
        )
    
    async def close(self):
        """Close client connection"""
        if self.client:
            await self.client.close_connection()
