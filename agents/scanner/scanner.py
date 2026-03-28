"""
Scanner Agent - Market Analysis and Signal Detection
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
import sqlite3

from .config import get_config, get_timeframes, get_pairs
from .binance_klines_client import BinanceKlinesClient
from agents.execution.binance_price_fetcher import BinancePriceFetcher


class Scanner:
    """
    Scanner Agent for detecting trading opportunities through technical analysis
    """
    
    def __init__(self):
        self.config = get_config()
        self.timeframes = get_timeframes()
        self.pairs = get_pairs()
        self.db_path = self.config["database_path"]
        self.use_real_data = self.config.get("use_real_market_data", True)
        
        # Initialize Binance price fetcher
        self.price_fetcher = BinancePriceFetcher(demo_mode=True)
        
        self.klines_client = None
        if self.use_real_data:
            self.klines_client = BinanceKlinesClient(demo_mode=True)
        
        # Setup logging
        logging.basicConfig(level=self.config["log_level"])
        self.logger = logging.getLogger(__name__)
    
    async def scan_market(self) -> Dict[str, Dict[str, any]]:
        """
        Scan all configured pairs across all timeframes
        
        Returns:
            Dict[str, Dict[str, any]]: Scan results organized by pair and timeframe
        """
        self.logger.info("Starting market scan...")
        results = {}
        
        for pair in self.pairs:
            results[pair] = {}
            self.logger.info(f"Scanning {pair}...")
            
            for timeframe in self.timeframes:
                try:
                    # Simulate fetching market data (in real implementation, this would come from API)
                    market_data = await self._fetch_market_data(pair, timeframe)
                    
                    if market_data is not None and len(market_data) > 0:
                        # Calculate indicators
                        indicators = self._calculate_indicators(market_data)
                        
                        # Detect trend changes
                        trend_change = self.detect_trend_change(indicators)
                        
                        # Get trading signal
                        signal = self.get_signal(indicators)
                        
                        # Store in results
                        results[pair][timeframe] = {
                            "timestamp": datetime.now().isoformat(),
                            "signal": signal,
                            "indicators": indicators,
                            "trend_change": trend_change
                        }
                        
                        # Store in database
                        await self._store_scan_result(pair, timeframe, signal, indicators)
                        
                        self.logger.info(f"Completed scan for {pair} on {timeframe}: {signal}")
                except Exception as e:
                    self.logger.error(f"Error scanning {pair} on {timeframe}: {str(e)}")
                    results[pair][timeframe] = {
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
        
        self.logger.info("Market scan completed")
        return results
    
    def _calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate various technical indicators
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with calculated indicators
        """
        df = data.copy()
        
        # Calculate Supertrend
        df = self.calculate_supertrend(df)
        
        # Calculate RSI
        df = self.calculate_rsi(df)
        
        # Calculate Simple Moving Average
        df = self.calculate_ma(df)
        
        # Calculate Exponential Moving Average
        df = self.calculate_ema(df)
        
        # Calculate MACD
        df = self.calculate_macd(df)
        
        return df
    
    def calculate_supertrend(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Supertrend indicator manually (ATR-based)
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with Supertrend values
        """
        period = self.config["supertrend"]["period"]
        multiplier = self.config["supertrend"]["multiplier"]
        
        # Calculate True Range (TR)
        df['prev_close'] = df['close'].shift(1)
        df['tr1'] = abs(df['high'] - df['low'])
        df['tr2'] = abs(df['high'] - df['prev_close'])
        df['tr3'] = abs(df['low'] - df['prev_close'])
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # Calculate Average True Range (ATR)
        df['atr'] = df['tr'].rolling(window=period).mean()
        
        # Calculate Basic Upper and Lower Bands
        df['upper_band'] = (df['high'] + df['low']) / 2 + multiplier * df['atr']
        df['lower_band'] = (df['high'] + df['low']) / 2 - multiplier * df['atr']
        
        # Initialize SuperTrend with NaN
        df['supertrend'] = np.nan
        df['direction'] = 1  # 1 for uptrend, -1 for downtrend
        
        # Set initial SuperTrend value
        df.loc[df.index[0], 'supertrend'] = df.loc[df.index[0], 'upper_band']
        
        # Calculate SuperTrend for subsequent bars
        for i in range(1, len(df)):
            prev_st = df.loc[df.index[i-1], 'supertrend']
            prev_direction = df.loc[df.index[i-1], 'direction']
            curr_upper = df.loc[df.index[i], 'upper_band']
            curr_lower = df.loc[df.index[i], 'lower_band']
            curr_high = df.loc[df.index[i], 'high']
            curr_low = df.loc[df.index[i], 'low']
            
            # Determine current direction based on previous ST and current price
            if prev_st == df.loc[df.index[i-1], 'upper_band']:
                # Previous was upper band (downtrend)
                if curr_low <= prev_st:
                    df.loc[df.index[i], 'supertrend'] = curr_upper
                    df.loc[df.index[i], 'direction'] = -1
                else:
                    df.loc[df.index[i], 'supertrend'] = prev_st
                    df.loc[df.index[i], 'direction'] = prev_direction
            elif prev_st == df.loc[df.index[i-1], 'lower_band']:
                # Previous was lower band (uptrend)
                if curr_high >= prev_st:
                    df.loc[df.index[i], 'supertrend'] = curr_lower
                    df.loc[df.index[i], 'direction'] = 1
                else:
                    df.loc[df.index[i], 'supertrend'] = prev_st
                    df.loc[df.index[i], 'direction'] = prev_direction
        
        # Clean up temporary columns
        df = df.drop(['prev_close', 'tr1', 'tr2', 'tr3', 'tr', 'upper_band', 'lower_band'], axis=1)
        
        return df
    
    def calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate RSI indicator manually
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with RSI values
        """
        period = self.config["rsi"]["period"]
        
        # Calculate price differences
        df['delta'] = df['close'].diff()
        
        # Get gains and losses
        df['gain'] = np.where(df['delta'] > 0, df['delta'], 0)
        df['loss'] = np.where(df['delta'] < 0, -df['delta'], 0)
        
        # Calculate average gain and loss using rolling average
        df['avg_gain'] = df['gain'].rolling(window=period, min_periods=1).mean()
        df['avg_loss'] = df['loss'].rolling(window=period, min_periods=1).mean()
        
        # Calculate RS (Relative Strength)
        df['rs'] = df['avg_gain'] / df['avg_loss']
        
        # Calculate RSI
        df['rsi'] = 100 - (100 / (1 + df['rs']))
        
        # Clean up temporary columns
        df = df.drop(['delta', 'gain', 'loss', 'avg_gain', 'avg_loss', 'rs'], axis=1)
        
        return df
    
    def calculate_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Simple Moving Average
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with MA values
        """
        df['ma'] = df['close'].rolling(window=20).mean()  # 20-period MA
        return df
    
    def calculate_ema(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Exponential Moving Average
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with EMA values
        """
        df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
        return df
    
    def calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            DataFrame with MACD values
        """
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        return df
    
    def detect_trend_change(self, df: pd.DataFrame) -> bool:
        """
        Detect if there's a trend change based on Supertrend
        
        Args:
            df: DataFrame with calculated indicators
            
        Returns:
            bool: True if trend change detected, False otherwise
        """
        if len(df) < 2 or 'direction' not in df.columns:
            return False
        
        # Check if the last two rows have different directions (indicating trend change)
        current_direction = df['direction'].iloc[-1]
        previous_direction = df['direction'].iloc[-2]
        
        # Handle NaN values properly
        if pd.isna(current_direction) or pd.isna(previous_direction):
            return False
        
        # Convert to Python bool to avoid numpy boolean issues
        return bool(current_direction != previous_direction)
    
    def get_signal(self, df: pd.DataFrame) -> float:
        """
        Generate trading signal based on indicators
        
        Args:
            df: DataFrame with calculated indicators
            
        Returns:
            float: Signal from -1.0 (strong SELL) to 1.0 (strong BUY)
        """
        if len(df) < 1:
            return 0.0
        
        signal_score = 0.0
        factors = 0
        
        last_row = df.iloc[-1]
        
        # Factor 1: Supertrend direction
        if 'direction' in df.columns:
            direction = last_row['direction']
            if direction == 1:
                signal_score += 0.4
            elif direction == -1:
                signal_score -= 0.4
            factors += 1
        
        # Factor 2: RSI
        if 'rsi' in df.columns:
            rsi = last_row['rsi']
            if not pd.isna(rsi):
                if rsi < 30:  # Oversold - potential buy signal
                    signal_score += 0.3
                elif rsi > 70:  # Overbought - potential sell signal
                    signal_score -= 0.3
                elif rsi < 45:
                    signal_score += 0.1
                elif rsi > 55:
                    signal_score -= 0.1
                factors += 1
        
        # Factor 3: Price relative to MA
        if 'ma' in df.columns and 'close' in df.columns:
            if not pd.isna(last_row['ma']):
                if last_row['close'] > last_row['ma']:
                    signal_score += 0.2
                else:
                    signal_score -= 0.2
                factors += 1
        
        # Factor 4: EMA crossover (EMA9 vs EMA21)
        if 'ema_9' in df.columns and 'ema_21' in df.columns:
            if not pd.isna(last_row['ema_9']) and not pd.isna(last_row['ema_21']):
                if last_row['ema_9'] > last_row['ema_21']:
                    signal_score += 0.2
                else:
                    signal_score -= 0.2
                factors += 1
        
        # Factor 5: MACD
        if 'macd' in df.columns and 'macd_signal' in df.columns:
            if not pd.isna(last_row['macd']) and not pd.isna(last_row['macd_signal']):
                if last_row['macd'] > last_row['macd_signal']:
                    signal_score += 0.2
                else:
                    signal_score -= 0.2
                factors += 1
        
        # Normalize signal to -1 to 1 range
        if factors > 0:
            normalized_signal = signal_score / min(factors, 1.5)
        else:
            normalized_signal = 0.0
        
        return round(max(-1.0, min(1.0, normalized_signal)), 3)
    
    async def _fetch_market_data(self, pair: str, timeframe: str) -> Optional[pd.DataFrame]:
        """
        Fetch market data for the given pair and timeframe
        
        Args:
            pair: Trading pair (e.g., BTC/USDT)
            timeframe: Timeframe (e.g., 5m, 1h)
            
        Returns:
            DataFrame with OHLCV data or None if unavailable
        """
        try:
            asset = pair.replace("/USDT", "").replace("-PERP", "")
            
            if self.use_real_data and self.klines_client is not None:
                try:
                    klines_df = await self.klines_client.get_klines(
                        symbol=asset, 
                        timeframe=timeframe, 
                        limit=100
                    )
                    if klines_df is not None and len(klines_df) >= 50:
                        self.logger.info(f"Fetched real klines data for {asset} on {timeframe}")
                        return klines_df
                    else:
                        self.logger.warning(f"Insufficient real klines data for {asset} on {timeframe}, falling back")
                except Exception as e:
                    self.logger.error(f"Real klines fetch failed for {asset} on {timeframe}: {e}")
            
            current_price = await self.price_fetcher.get_price(asset)
            
            if current_price is None or current_price == 0:
                self.logger.warning(f"Could not fetch real price for {asset}, using fallback")
                current_price = 50000.0
            
            n_samples = 100
            
            freq_map = {
                "1m": "min", "5m": "5min", "15m": "15min", 
                "1h": "h", "4h": "4h", "1d": "D"
            }
            freq = freq_map.get(timeframe, "min")
            
            dates = pd.date_range(end=datetime.now(), periods=n_samples, freq=freq)
            
            volatility = current_price * 0.002
            close_prices = current_price + np.random.randn(n_samples).cumsum() * volatility
            
            open_prices = close_prices + np.random.randn(n_samples) * volatility * 0.5
            high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.randn(n_samples)) * volatility
            low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.randn(n_samples)) * volatility
            
            volume = np.abs(np.random.randn(n_samples)) * 1000 + 500
            
            data = pd.DataFrame({
                'timestamp': dates,
                'open': open_prices,
                'high': high_prices,
                'low': low_prices,
                'close': close_prices,
                'volume': volume
            })
            
            return data
        except Exception as e:
            self.logger.error(f"Error fetching market data for {pair} on {timeframe}: {str(e)}")
            return None
    
    async def _store_scan_result(self, pair: str, timeframe: str, signal, indicators: pd.DataFrame) -> None:
        """
        Store scan result in database
        
        Args:
            pair: Trading pair
            timeframe: Timeframe
            signal: Trading signal (can be float or string)
            indicators: DataFrame with calculated indicators
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get the latest close price and supertrend value
            latest_close = indicators['close'].iloc[-1] if 'close' in indicators.columns else None
            supertrend_value = indicators['supertrend'].iloc[-1] if 'supertrend' in indicators.columns else None
            confidence = 0.8
            
            # Convert numeric signal to string if needed
            signal_str = signal
            if isinstance(signal, (int, float)):
                signal_str = self.signal_to_string(signal)
            
            # Insert scan result
            cursor.execute("""
                INSERT INTO scan_cache (pair, signal, confidence, price, supertrend_value)
                VALUES (?, ?, ?, ?, ?)
            """, (pair, signal_str, confidence, latest_close, supertrend_value))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Stored scan result for {pair} on {timeframe}")
        except Exception as e:
            self.logger.error(f"Error storing scan result for {pair} on {timeframe}: {str(e)}")
    
    def signal_to_string(self, signal: float) -> str:
        """
        Convert numeric signal to string representation for database storage.
        
        Args:
            signal: Numeric signal (-1.0 to 1.0)
            
        Returns:
            str: Signal as string ("BUY", "SELL", "HOLD")
        """
        if signal > 0.2:
            return "BUY"
        elif signal < -0.2:
            return "SELL"
        else:
            return "HOLD"
    
    async def get_latest_signals(self) -> Dict[str, str]:
        """
        Get the latest trading signals for all pairs
        
        Returns:
            Dict[str, str]: Dictionary mapping pairs to their latest signals
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            signals = {}
            for pair in self.pairs:
                cursor.execute("""
                    SELECT signal FROM scan_cache 
                    WHERE pair = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, (pair,))
                
                result = cursor.fetchone()
                if result:
                    signals[pair] = result[0]
                else:
                    signals[pair] = "HOLD"  # Default signal
            
            conn.close()
            return signals
        except Exception as e:
            self.logger.error(f"Error getting latest signals: {str(e)}")
            return {pair: "HOLD" for pair in self.pairs}