"""
Binance Price Fetcher
Simple price fetching using python-binance library
"""
import asyncio
import logging
from typing import Optional
from binance import AsyncClient

logger = logging.getLogger(__name__)


class BinancePriceFetcher:
    """Fetch prices from Binance (Demo/Testnet/Mainnet)"""
    
    def __init__(self, demo_mode: bool = True, api_key: str = "", api_secret: str = ""):
        """
        Initialize Binance Price Fetcher
        
        Args:
            demo_mode: Use demo API (True) or mainnet (False)
            api_key: Optional API key (not needed for public endpoints)
            api_secret: Optional API secret (not needed for public endpoints)
        """
        self.demo_mode = demo_mode
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the Binance client"""
        if self._initialized:
            return
        
        try:
            if self.api_key and self.api_secret:
                # Authenticated client
                self.client = await AsyncClient.create(
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    demo=self.demo_mode
                )
            else:
                # Public client (no auth needed for price fetching)
                self.client = AsyncClient()
                if self.demo_mode:
                    # For demo mode without auth, we'll use testnet
                    self.client = await AsyncClient.create(
                        api_key='dummy',
                        api_secret='dummy',
                        testnet=True
                    )
            
            self._initialized = True
            logger.info(f"Binance Price Fetcher initialized (demo={self.demo_mode})")
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
            # Fallback to public client
            self.client = AsyncClient()
            self._initialized = True
    
    async def get_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol
        
        Args:
            symbol: Asset symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Current price in USDT or None if error
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # Convert symbol to Binance format (e.g., BTC -> BTCUSDT)
            binance_symbol = f"{symbol}USDT"
            
            # Get ticker price
            ticker = await self.client.get_symbol_ticker(symbol=binance_symbol)
            price = float(ticker.get('price', 0))
            
            if price > 0:
                logger.debug(f"{symbol} price: ${price:.2f}")
                return price
            else:
                logger.warning(f"Invalid price for {symbol}: {price}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    async def get_prices(self, symbols: list) -> dict:
        """
        Get prices for multiple symbols
        
        Args:
            symbols: List of asset symbols
            
        Returns:
            Dict of {symbol: price}
        """
        prices = {}
        for symbol in symbols:
            price = await self.get_price(symbol)
            if price:
                prices[symbol] = price
        return prices
    
    async def close(self):
        """Close the client connection"""
        if self.client and hasattr(self.client, 'close_connection'):
            await self.client.close_connection()
            self._initialized = False


# Singleton instance for easy import
_price_fetcher = None

def get_price_fetcher(demo_mode: bool = True) -> BinancePriceFetcher:
    """Get or create the singleton price fetcher instance"""
    global _price_fetcher
    if _price_fetcher is None:
        _price_fetcher = BinancePriceFetcher(demo_mode=demo_mode)
    return _price_fetcher
