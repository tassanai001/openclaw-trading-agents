"""
Scanner Configuration Module
"""
import os
from typing import List, Dict, Any
from config.trading_config import TRADING_CONFIG

# Scanner Configuration
SCANNER_CONFIG = {
    # Timeframes to scan (in minutes)
    "timeframes": ["5m", "15m", "1h", "4h", "1d"],
    
    # Supertrend parameters
    "supertrend": {
        "period": 10,      # ATR period
        "multiplier": 3.0  # Multiplier for ATR
    },
    
    # RSI parameters
    "rsi": {
        "period": 14       # RSI calculation period
    },
    
    # Pairs to scan
    "pairs": TRADING_CONFIG["pairs"],
    
    # Database connection
    "database_path": os.getenv("DATABASE_PATH", "data/state.db"),
    
    # Logging
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
    
    "use_real_market_data": os.getenv("USE_REAL_MARKET_DATA", "true").lower() == "true",
}

def get_config() -> Dict[str, Any]:
    """
    Get scanner configuration
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    return SCANNER_CONFIG

def get_timeframes() -> List[str]:
    """
    Get configured timeframes
    
    Returns:
        List[str]: List of timeframes to scan
    """
    return SCANNER_CONFIG["timeframes"]

def get_pairs() -> List[str]:
    """
    Get configured trading pairs
    
    Returns:
        List[str]: List of trading pairs to scan
    """
    return SCANNER_CONFIG["pairs"]