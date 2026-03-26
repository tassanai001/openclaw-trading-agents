"""
Hyperliquid API wrapper using official hyperliquid-python-sdk
"""
import asyncio
import time
import logging
from typing import Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class HyperliquidAPI:
    """Wrapper for Hyperliquid API using official SDK"""
    
    def __init__(self, api_key: str, secret: str, is_testnet: bool = True, mock_mode: bool = False, wallet_address: Optional[str] = None):
        """
        Initialize Hyperliquid API
        
        Args:
            api_key: API key (for SDK this is the wallet address)
            secret: API secret (private key)
            is_testnet: Use testnet or mainnet
            mock_mode: Use mock responses for testing
            wallet_address: Optional wallet address for vault/subaccount operations
        """
        self.api_key = api_key
        self.secret = secret
        self.is_testnet = is_testnet
        self.mock_mode = mock_mode
        self.wallet_address = wallet_address or api_key
        
        # Import SDK
        try:
            from hyperliquid.info import Info
            from hyperliquid.exchange import Exchange
            
            # Initialize Info (for reading data - no auth needed)
            self.info = Info() if is_testnet else Info(mainnet=True)
            
            # Initialize Exchange (for trading - needs auth)
            if is_testnet:
                self.exchange = Exchange(secret, wallet_address=api_key)
            else:
                self.exchange = Exchange(secret, wallet_address=api_key, mainnet=True)
                
            logger.info(f"Hyperliquid SDK initialized (testnet={is_testnet}, mock={mock_mode})")
        except ImportError as e:
            logger.error(f"Failed to import hyperliquid-python-sdk: {e}")
            raise
        
    async def close(self):
        """Close any open connections"""
        pass  # SDK handles cleanup internally
    
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place an order on Hyperliquid using official SDK
        
        Args:
            order_data: Dict with keys:
                - asset: Asset name (e.g., "BTC", "ETH")
                - is_buy: True for buy, False for sell
                - size: Order size
                - price: Price (for limit orders) or None for market
                - order_type: "limit" or "market"
                - reduce_only: True/False
                
        Returns:
            Dict with order result
        """
        if self.mock_mode:
            logger.info("Mock mode: simulating order")
            return {
                "status": "success",
                "order_id": f"mock_{int(time.time())}",
                "timestamp": time.time(),
                "order": order_data,
                "fills": []
            }
        
        try:
            asset = order_data.get("asset", "BTC")
            is_buy = order_data.get("is_buy", True)
            size = float(order_data.get("size", 0.01))
            price = order_data.get("price")
            order_type = order_data.get("order_type", "market")
            reduce_only = order_data.get("reduce_only", False)
            
            logger.info(f"Placing {order_type} order: {'BUY' if is_buy else 'SELL'} {size} {asset} @ {price or 'MARKET'}")
            
            # Place order using SDK
            if order_type == "market":
                # Market order
                result = self.exchange.market_open(
                    asset,
                    is_buy=is_buy,
                    sz=size,
                    reduce_only=reduce_only
                )
            else:
                # Limit order
                if price is None:
                    raise ValueError("Price required for limit order")
                result = self.exchange.limit_open(
                    asset,
                    is_buy=is_buy,
                    sz=size,
                    px=float(price),
                    reduce_only=reduce_only
                )
            
            logger.info(f"Order placed successfully: {result}")
            
            return {
                "status": "success",
                "order_id": result.get("order_id", str(result)),
                "timestamp": time.time(),
                "order": order_data,
                "fills": result.get("fills", []),
                "raw_response": result
            }
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def cancel_order(self, order_id: str, asset: str = "BTC") -> Dict[str, Any]:
        """Cancel an order"""
        if self.mock_mode:
            return {
                "status": "success",
                "order_id": order_id,
                "cancelled": True
            }
        
        try:
            result = self.exchange.cancel(asset, order_id)
            return {
                "status": "success",
                "order_id": order_id,
                "cancelled": True,
                "raw_response": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_open_orders(self, asset: Optional[str] = None) -> Dict[str, Any]:
        """Get open orders"""
        if self.mock_mode:
            return {"open_orders": [], "timestamp": time.time()}
        
        try:
            # Get from info endpoint (no auth needed)
            orders = self.info.open_orders(self.wallet_address)
            if asset:
                orders = [o for o in orders if o.get("coin") == asset]
            return {
                "open_orders": orders,
                "timestamp": time.time()
            }
        except Exception as e:
            return {"open_orders": [], "error": str(e)}
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        if self.mock_mode:
            return {
                "account_value": 10000.0,
                "balances": [{"coin": "USDC", "amount": 5000.0}],
                "positions": []
            }
        
        try:
            # Get account value
            account_data = self.info.user_state(self.wallet_address)
            
            account_value = float(account_data.get("marginSummary", {}).get("accountValue", 0))
            balances = account_data.get("assetPositions", [])
            
            return {
                "account_value": account_value,
                "balances": balances,
                "positions": account_data.get("assetPositions", []),
                "raw_response": account_data
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {"account_value": 0, "balances": [], "error": str(e)}
    
    async def get_positions(self) -> Dict[str, Any]:
        """Get current positions"""
        if self.mock_mode:
            return {"positions": []}
        
        try:
            account_data = self.info.user_state(self.wallet_address)
            positions = account_data.get("assetPositions", [])
            return {
                "positions": positions,
                "timestamp": time.time()
            }
        except Exception as e:
            return {"positions": [], "error": str(e)}
    
    async def get_balance(self, coin: str = "USDC") -> float:
        """Get balance for a specific coin"""
        if self.mock_mode:
            return 10000.0
        
        try:
            account_data = self.info.user_state(self.wallet_address)
            balances = account_data.get("balances", [])
            
            for balance in balances:
                if balance.get("coin") == coin:
                    return float(balance.get("sz", 0))
            
            return 0.0
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0.0


class PriceFetcher:
    """Fetch prices from Hyperliquid"""
    
    def __init__(self, is_testnet: bool = True):
        self.is_testnet = is_testnet
        try:
            from hyperliquid.info import Info
            self.info = Info() if is_testnet else Info(mainnet=True)
        except ImportError:
            self.info = None
    
    async def get_price(self, asset: str) -> float:
        """Get current price for an asset"""
        if self.info is None:
            return 0.0
        
        try:
            # Get all coin prices
            all_prices = self.info.all_mids()
            
            # Map asset name to format expected by API
            asset_key = asset.upper()
            if not asset_key.endswith("USD"):
                asset_key = f"{asset_key}USD"
            
            if asset_key in all_prices:
                return float(all_prices[asset_key])
            
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching price for {asset}: {e}")
            return 0.0
    
    async def get_all_prices(self) -> Dict[str, float]:
        """Get all market prices"""
        if self.info is None:
            return {}
        
        try:
            all_prices = self.info.all_mids()
            return {k: float(v) for k, v in all_prices.items()}
        except Exception as e:
            logger.error(f"Error fetching all prices: {e}")
            return {}
