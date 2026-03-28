"""
Liquidity Checker for real order book-based liquidity validation
"""
import asyncio
import logging
from typing import Optional, Tuple, Dict, List

logger = logging.getLogger(__name__)


class LiquidityChecker:
    """Real liquidity checker using order book data"""
    
    def __init__(self, exchange: str, config):
        self.exchange = exchange.lower()
        self.config = config
        self._binance_adapter = None
        self._hyperliquid_api = None
        
    async def check_liquidity(self, symbol: str, side: str, required_size: float) -> Tuple[bool, float]:
        """
        Check if there's sufficient liquidity for the order within 1% of mid-price
        
        Args:
            symbol: Trading pair
            side: "buy" or "sell"
            required_size: Required order size in base asset
            
        Returns:
            Tuple of (is_sufficient: bool, available_size: float)
        """
        try:
            if self.exchange == "binance":
                return await self._check_binance_liquidity(symbol, side, required_size)
            elif self.exchange == "hyperliquid":
                return await self._check_hyperliquid_liquidity(symbol, side, required_size)
            else:
                logger.warning(f"Unsupported exchange {self.exchange} for liquidity check")
                return False, 0.0
                
        except Exception as e:
            logger.error(f"Error checking liquidity for {symbol}: {e}")
            return False, 0.0
    
    async def _check_binance_liquidity(self, symbol: str, side: str, required_size: float) -> Tuple[bool, float]:
        from .adapters.base import ExchangeCredentials
        from .adapters.binance import BinanceAdapter
        
        if not self._binance_adapter:
            credentials = ExchangeCredentials(
                api_key="",
                api_secret="",
                testnet=self.config.is_testnet,
                demo_mode=getattr(self.config, 'demo_mode', False)
            )
            self._binance_adapter = BinanceAdapter(credentials)
            await self._binance_adapter.initialize()
        
        order_book = await self._binance_adapter.client.get_order_book(
            symbol=symbol.upper(), 
            limit=100
        )
        ticker = await self._binance_adapter.client.get_symbol_ticker(symbol=symbol.upper())
        current_price = float(ticker["price"])
        
        price_range = current_price * 0.01
        min_price = current_price - price_range
        max_price = current_price + price_range
        
        available_size = 0.0
        
        if side.lower() == "buy":
            for price_level, size_level in order_book.get("asks", []):
                if price_level <= max_price:
                    available_size += size_level
                else:
                    break
        else:
            for price_level, size_level in order_book.get("bids", []):
                if price_level >= min_price:
                    available_size += size_level
                else:
                    break
        
        available_usd = available_size * current_price
        min_liquidity_usd = getattr(self.config, 'min_liquidity_usd', 50000.0)
        
        is_sufficient = available_usd >= min_liquidity_usd and available_size >= required_size
        return is_sufficient, available_size
    
    async def _check_hyperliquid_liquidity(self, symbol: str, side: str, required_size: float) -> Tuple[bool, float]:
        from .hyperliquid_api import HyperliquidAPI
        
        if not self._hyperliquid_api:
            self._hyperliquid_api = HyperliquidAPI(
                api_key="dummy",
                secret="dummy",
                is_testnet=self.config.is_testnet,
                mock_mode=False
            )
        
        clean_symbol = symbol.replace("USDT", "") if "USDT" in symbol else symbol
        order_book = self._hyperliquid_api.info.l2Book(clean_symbol)
        ticker_data = self._hyperliquid_api.info.all_mids()
        current_price = float(ticker_data.get(clean_symbol, 0))
        if current_price == 0:
            raise ValueError(f"Could not get price for {clean_symbol}")
        
        bids = []
        asks = []
        for level in order_book.get("levels", []):
            if len(level) >= 2:
                price_level = float(level[0]["px"])
                size_level = float(level[0]["sz"])
                if price_level < current_price:
                    bids.append([price_level, size_level])
                else:
                    asks.append([price_level, size_level])
        
        bids.sort(key=lambda x: x[0], reverse=True)
        asks.sort(key=lambda x: x[0])
        
        price_range = current_price * 0.01
        min_price = current_price - price_range
        max_price = current_price + price_range
        
        available_size = 0.0
        
        if side.lower() == "buy":
            for price_level, size_level in asks:
                if price_level <= max_price:
                    available_size += size_level
                else:
                    break
        else:
            for price_level, size_level in bids:
                if price_level >= min_price:
                    available_size += size_level
                else:
                    break
        
        available_usd = available_size * current_price
        min_liquidity_usd = getattr(self.config, 'min_liquidity_usd', 50000.0)
        
        is_sufficient = available_usd >= min_liquidity_usd and available_size >= required_size
        return is_sufficient, available_size