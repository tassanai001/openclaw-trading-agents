import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from binance import AsyncClient, BinanceAPIException
from binance.exceptions import BinanceRequestException

logger = logging.getLogger(__name__)

TIMEFRAME_MAP = {
    "1m": "1m",
    "5m": "5m", 
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d"
}

MAX_REQUESTS_PER_MINUTE = 1200
REQUEST_INTERVAL = 60.0 / MAX_REQUESTS_PER_MINUTE

class BinanceKlinesClient:
    
    def __init__(self, demo_mode: bool = True, api_key: str = "", api_secret: str = ""):
        self.demo_mode = demo_mode
        self.api_key = api_key or os.getenv("BINANCE_API_KEY", "")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET", "")
        self.client = None
        self._initialized = False
        
        self._last_request_time = 0.0
        self._request_lock = asyncio.Lock()
        
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = 30.0
        
    async def initialize(self):
        if self._initialized:
            return
            
        try:
            if self.api_key and self.api_secret:
                self.client = await AsyncClient.create(
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    demo=self.demo_mode
                )
            else:
                if self.demo_mode:
                    self.client = await AsyncClient.create(
                        api_key='dummy',
                        api_secret='dummy', 
                        testnet=True
                    )
                else:
                    self.client = AsyncClient()
                    
            self._initialized = True
            logger.info(f"Binance Klines Client initialized (demo={self.demo_mode})")
            
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
            raise
            
    async def _rate_limit(self):
        async with self._request_lock:
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self._last_request_time
            
            if time_since_last < REQUEST_INTERVAL:
                sleep_time = REQUEST_INTERVAL - time_since_last
                await asyncio.sleep(sleep_time)
                
            self._last_request_time = asyncio.get_event_loop().time()
            
    def _get_cache_key(self, symbol: str, timeframe: str, limit: int) -> str:
        return f"{symbol}_{timeframe}_{limit}"
        
    def _get_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        if cache_key in self._cache:
            df, timestamp = self._cache[cache_key]
            if asyncio.get_event_loop().time() - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for {cache_key}")
                return df
            else:
                del self._cache[cache_key]
                logger.debug(f"Cache expired for {cache_key}")
                
        return None
        
    def _set_cache(self, cache_key: str, df: pd.DataFrame):
        self._cache[cache_key] = (df, asyncio.get_event_loop().time())
        logger.debug(f"Cache set for {cache_key}")
        
    async def get_klines(
        self, 
        symbol: str, 
        timeframe: str, 
        limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        Fetch klines data from Binance API.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            timeframe: Timeframe string ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of candles to fetch (default: 100, max: 1000)
            
        Returns:
            pd.DataFrame with columns: timestamp, open, high, low, close, volume
            or None if failed
        """
        if timeframe not in TIMEFRAME_MAP:
            logger.error(f"Invalid timeframe: {timeframe}. Supported: {list(TIMEFRAME_MAP.keys())}")
            return None
            
        if limit < 1 or limit > 1000:
            logger.error(f"Invalid limit: {limit}. Must be between 1-1000")
            return None
            
        binance_symbol = symbol.upper()
        if not binance_symbol.endswith("USDT"):
            binance_symbol = f"{binance_symbol}USDT"
            
        cache_key = self._get_cache_key(binance_symbol, timeframe, limit)
        cached_df = self._get_from_cache(cache_key)
        if cached_df is not None:
            return cached_df.copy()
            
        if not self._initialized:
            await self.initialize()
            
        await self._rate_limit()
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Fetching klines for {binance_symbol} on {timeframe}, attempt {attempt + 1}")
                
                klines = await self.client.get_klines(
                    symbol=binance_symbol,
                    interval=TIMEFRAME_MAP[timeframe],
                    limit=limit
                )
                
                if not klines:
                    logger.warning(f"No klines data returned for {binance_symbol} on {timeframe}")
                    return None
                    
                df = self._klines_to_dataframe(klines)
                
                if df is not None and len(df) > 0:
                    self._set_cache(cache_key, df)
                    return df
                    
            except BinanceAPIException as e:
                logger.error(f"Binance API error for {binance_symbol} on {timeframe}: {e}")
                if e.code == -1003:
                    delay = base_delay * (2 ** attempt) + 5.0
                elif e.code == -1121:
                    logger.error(f"Invalid symbol: {binance_symbol}")
                    return None
                else:
                    delay = base_delay * (2 ** attempt)
                    
            except BinanceRequestException as e:
                logger.error(f"Binance request error for {binance_symbol} on {timeframe}: {e}")
                delay = base_delay * (2 ** attempt)
                
            except ConnectionError as e:
                logger.error(f"Connection error for {binance_symbol} on {timeframe}: {e}")
                delay = base_delay * (2 ** attempt)
                
            except Exception as e:
                logger.error(f"Unexpected error fetching klines for {binance_symbol} on {timeframe}: {e}")
                delay = base_delay * (2 ** attempt)
                
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)
                
        logger.error(f"Failed to fetch klines for {binance_symbol} on {timeframe} after {max_retries} attempts")
        return None
        
    def _klines_to_dataframe(self, klines: List[List]) -> pd.DataFrame:
        if not klines:
            return pd.DataFrame()
            
        data = []
        for kline in klines:
            if len(kline) >= 6:
                timestamp = datetime.fromtimestamp(kline[0] / 1000.0)
                open_price = float(kline[1])
                high_price = float(kline[2])
                low_price = float(kline[3])
                close_price = float(kline[4])
                volume = float(kline[5])
                
                data.append({
                    'timestamp': timestamp,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                })
                
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        return df
        
    async def close(self):
        if self.client and hasattr(self.client, 'close_connection'):
            await self.client.close_connection()
            self._initialized = False
            logger.info("Binance Klines Client connection closed")
            
    async def get_multiple_timeframes(
        self, 
        symbol: str, 
        timeframes: List[str], 
        limit: int = 100
    ) -> Dict[str, Optional[pd.DataFrame]]:
        tasks = [
            self.get_klines(symbol, timeframe, limit) 
            for timeframe in timeframes 
            if timeframe in TIMEFRAME_MAP
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        timeframe_results = {}
        valid_timeframes = [tf for tf in timeframes if tf in TIMEFRAME_MAP]
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {valid_timeframes[i]}: {result}")
                timeframe_results[valid_timeframes[i]] = None
            else:
                timeframe_results[valid_timeframes[i]] = result
                
        return timeframe_results