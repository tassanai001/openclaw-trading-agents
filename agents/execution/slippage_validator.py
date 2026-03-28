"""
Slippage Validator for real order book-based slippage calculation
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class SlippageValidator:
    """Real slippage calculator using order book data"""
    
    def __init__(self, exchange: str, config):
        self.exchange = exchange.lower()
        self.config = config
        self._binance_adapter = None
        self._hyperliquid_api = None
        
    async def get_slippage(self, symbol: str, side: str, size: float, price: Optional[float] = None) -> float:
        try:
            if self.exchange == "binance":
                return await self._get_binance_slippage(symbol, side, size, price)
            elif self.exchange == "hyperliquid":
                return await self._get_hyperliquid_slippage(symbol, side, size, price)
            else:
                logger.warning(f"Unsupported exchange {self.exchange} for slippage calculation")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating slippage for {symbol}: {e}")
            return 10.0
    
    async def _get_binance_slippage(self, symbol: str, side: str, size: float, price: Optional[float]) -> float:
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
        
        if price is None:
            ticker = await self._binance_adapter.client.get_symbol_ticker(symbol=symbol.upper())
            price = float(ticker["price"])
        
        vwap = await self._calculate_vwap_from_orderbook(
            order_book, side, size, price
        )
        
        mid_price = price
        if vwap == 0:
            return 0.0
            
        slippage = abs((vwap - mid_price) / mid_price * 100)
        return slippage
    
    async def _get_hyperliquid_slippage(self, symbol: str, side: str, size: float, price: Optional[float]) -> float:
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
        
        if price is None:
            ticker_data = self._hyperliquid_api.info.all_mids()
            price = float(ticker_data.get(clean_symbol, 0))
            if price == 0:
                raise ValueError(f"Could not get price for {clean_symbol}")
        
        bids = []
        asks = []
        for level in order_book.get("levels", []):
            if len(level) >= 2:
                price_level = float(level[0]["px"])
                size_level = float(level[0]["sz"])
                if price_level < price:
                    bids.append([price_level, size_level])
                else:
                    asks.append([price_level, size_level])
        
        bids.sort(key=lambda x: x[0], reverse=True)
        asks.sort(key=lambda x: x[0])
        
        standard_order_book = {
            "bids": bids,
            "asks": asks
        }
        
        vwap = await self._calculate_vwap_from_orderbook(
            standard_order_book, side, size, price
        )
        
        mid_price = price
        if vwap == 0:
            return 0.0
            
        slippage = abs((vwap - mid_price) / mid_price * 100)
        return slippage
    
    async def _calculate_vwap_from_orderbook(
        self, 
        order_book: Dict[str, List[List[float]]], 
        side: str, 
        target_size: float, 
        current_price: float
    ) -> float:
        total_value = 0.0
        total_size = 0.0
        
        if side.lower() == "buy":
            levels = order_book.get("asks", [])
            for price_level, size_level in levels:
                if total_size >= target_size:
                    break
                remaining_size = target_size - total_size
                take_size = min(size_level, remaining_size)
                total_value += price_level * take_size
                total_size += take_size
                
        else:
            levels = order_book.get("bids", [])
            for price_level, size_level in levels:
                if total_size >= target_size:
                    break
                remaining_size = target_size - total_size
                take_size = min(size_level, remaining_size)
                total_value += price_level * take_size
                total_size += take_size
        
        if total_size == 0:
            return current_price
        
        return total_value / total_size