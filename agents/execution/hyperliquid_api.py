"""
Hyperliquid API wrapper for the Execution Agent
"""
import asyncio
import json
import time
import hashlib
import hmac
from typing import Dict, Any, Optional
import httpx


class HyperliquidAPI:
    """Wrapper for Hyperliquid API interactions"""
    
    def __init__(self, api_key: str, secret: str, is_testnet: bool = True, mock_mode: bool = False):
        self.api_key = api_key
        self.secret = secret
        self.is_testnet = is_testnet
        self.mock_mode = mock_mode
        
        if is_testnet:
            self.base_url = "https://api.hyperliquid-testnet.xyz"
        else:
            self.base_url = "https://api.hyperliquid.xyz"
        
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    def _sign_request(self, payload: str, timestamp: int) -> str:
        """Sign request with HMAC"""
        signature_string = f"{timestamp}{payload}"
        signature = hmac.new(
            self.secret.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place an order on Hyperliquid"""
        if self.mock_mode:
            # Mock response for testing
            return {
                "status": "success",
                "order_id": f"mock_{int(time.time())}",
                "timestamp": time.time(),
                "order": order_data,
                "fills": []
            }
        
        payload = {
            "action": "place_order",
            "order": order_data,
            "timestamp": int(time.time() * 1000)
        }
        
        timestamp = payload["timestamp"]
        signature = self._sign_request(json.dumps(payload, separators=(',', ':')), timestamp)
        
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
            "X-SIGNATURE": signature,
            "X-TIMESTAMP": str(timestamp)
        }
        
        response = await self.client.post(f"{self.base_url}/v1/order", 
                                         json=payload, 
                                         headers=headers)
        response.raise_for_status()
        return response.json()
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order on Hyperliquid"""
        if self.mock_mode:
            # Mock response for testing
            return {
                "status": "success",
                "order_id": order_id,
                "cancelled": True
            }
        
        payload = {
            "action": "cancel_order",
            "order_id": order_id,
            "timestamp": int(time.time() * 1000)
        }
        
        timestamp = payload["timestamp"]
        signature = self._sign_request(json.dumps(payload, separators=(',', ':')), timestamp)
        
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
            "X-SIGNATURE": signature,
            "X-TIMESTAMP": str(timestamp)
        }
        
        response = await self.client.post(f"{self.base_url}/v1/cancel", 
                                         json=payload, 
                                         headers=headers)
        response.raise_for_status()
        return response.json()
    
    async def get_open_orders(self, asset: Optional[str] = None) -> Dict[str, Any]:
        """Get open orders from Hyperliquid"""
        if self.mock_mode:
            # Mock response for testing
            return {
                "open_orders": [],
                "timestamp": time.time()
            }
        
        payload = {
            "action": "get_open_orders",
            "asset": asset or "ALL",
            "timestamp": int(time.time() * 1000)
        }
        
        timestamp = payload["timestamp"]
        signature = self._sign_request(json.dumps(payload, separators=(',', ':')), timestamp)
        
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
            "X-SIGNATURE": signature,
            "X-TIMESTAMP": str(timestamp)
        }
        
        response = await self.client.post(f"{self.base_url}/v1/orders", 
                                         json=payload, 
                                         headers=headers)
        response.raise_for_status()
        return response.json()
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information from Hyperliquid"""
        if self.mock_mode:
            # Mock response for testing
            return {
                "account_value": 10000.0,
                "balances": [
                    {"coin": "USDC", "amount": 5000.0},
                    {"coin": "BTC", "amount": 0.1}
                ],
                "positions": [],
                "timestamp": time.time()
            }
        
        payload = {
            "action": "get_account_info",
            "timestamp": int(time.time() * 1000)
        }
        
        timestamp = payload["timestamp"]
        signature = self._sign_request(json.dumps(payload, separators=(',', ':')), timestamp)
        
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
            "X-SIGNATURE": signature,
            "X-TIMESTAMP": str(timestamp)
        }
        
        response = await self.client.post(f"{self.base_url}/v1/account", 
                                         json=payload, 
                                         headers=headers)
        response.raise_for_status()
        return response.json()

    async def get_all_market_prices(self) -> Dict[str, Dict[str, float]]:
        """
        Fetch all market prices from Hyperliquid info endpoint.
        
        Returns:
            Dict mapping asset names to price data (e.g., {"BTC": {"price": 50000.0, "bid": ..., "ask": ...}})
        """
        try:
            response = await self.client.get(f"{self.base_url}/info/all")
            response.raise_for_status()
            data = response.json()
            
            prices = {}
            
            if "universe" in data:
                for asset_data in data.get("universe", []):
                    name = asset_data.get("name", "")
                    if name:
                        prices[name] = {"price": asset_data.get("px", 0.0)}
            
            if "prices" in data:
                for token_data in data.get("prices", []):
                    symbol = token_data.get("token", "")
                    price = token_data.get("px", 0.0)
                    if symbol:
                        prices[symbol] = {"price": price}
            
            return prices
        except Exception as e:
            return {}
    
    async def get_price(self, asset: str) -> Optional[float]:
        """
        Get current price for a specific asset.
        
        Args:
            asset: Asset symbol (e.g., "BTC", "ETH")
            
        Returns:
            Current price or None if unavailable
        """
        prices = await self.get_all_market_prices()
        
        asset_normalized = asset.upper().replace("/USDT", "").replace("-PERP", "")
        
        if asset_normalized in prices:
            return prices[asset_normalized].get("price")
        
        for symbol, price_data in prices.items():
            if symbol.upper() == asset_normalized:
                return price_data.get("price")
        
        return None


class PriceFetcher:
    """Standalone price fetcher for market data (no auth required)"""
    
    def __init__(self, is_testnet: bool = True):
        self.is_testnet = is_testnet
        if is_testnet:
            self.base_url = "https://api.hyperliquid-testnet.xyz"
        else:
            self.base_url = "https://api.hyperliquid.xyz"
        self.client = httpx.AsyncClient(timeout=30.0)
        self._cached_prices: Dict[str, float] = {}
        self._cache_time: float = 0
        self._cache_ttl: float = 60
    
    async def close(self):
        await self.client.aclose()
    
    async def _fetch_all_prices(self) -> Dict[str, float]:
        """Fetch all prices from the API"""
        try:
            current_time = time.time()
            if self._cached_prices and (current_time - self._cache_time) < self._cache_ttl:
                return self._cached_prices
            
            response = await self.client.get(f"{self.base_url}/info/all")
            response.raise_for_status()
            data = response.json()
            
            prices = {}
            
            if isinstance(data, dict):
                if "universe" in data:
                    for asset_data in data.get("universe", []):
                        name = asset_data.get("name", "")
                        px = asset_data.get("px")
                        if name and px:
                            prices[name] = float(px)
                
                if "prices" in data:
                    for token_data in data.get("prices", []):
                        symbol = token_data.get("token", "")
                        px = token_data.get("px")
                        if symbol and px:
                            prices[symbol] = float(px)
            
            self._cached_prices = prices
            self._cache_time = current_time
            
            return prices
        except Exception:
            return self._cached_prices if self._cached_prices else {}
    
    async def get_price(self, asset: str) -> Optional[float]:
        """
        Get current price for an asset.
        
        Args:
            asset: Asset symbol (e.g., "BTC", "ETH", "BTC/USDT")
            
        Returns:
            Current price or None if unavailable
        """
        prices = await self._fetch_all_prices()
        
        asset_normalized = asset.upper().replace("/USDT", "").replace("-PERP", "").replace("PERP", "")
        
        if asset_normalized in prices:
            return prices[asset_normalized]
        
        for symbol, price in prices.items():
            if symbol.upper() == asset_normalized:
                return price
        
        return None
    
    async def get_prices_for_pairs(self, pairs: list[str]) -> Dict[str, Optional[float]]:
        """Get prices for multiple trading pairs."""
        result = {}
        for pair in pairs:
            result[pair] = await self.get_price(pair)
        return result
    
    def clear_cache(self):
        """Clear cached prices"""
        self._cached_prices = {}
        self._cache_time = 0