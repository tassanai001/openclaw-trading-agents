"""
Tests for Scanner Agent
"""
import asyncio
import pytest
import pytest_asyncio
import pandas as pd
import numpy as np
from datetime import datetime

from agents.scanner.scanner import Scanner
from agents.scanner.config import get_config


@pytest_asyncio.fixture
async def scanner():
    """Create a Scanner instance for testing"""
    scanner_instance = Scanner()
    yield scanner_instance


@pytest.mark.asyncio
async def test_scanner_initialization(scanner):
    """Test Scanner initialization"""
    assert scanner is not None
    assert scanner.config is not None
    assert scanner.timeframes is not None
    assert scanner.pairs is not None


@pytest.mark.asyncio
async def test_calculate_rsi():
    """Test RSI calculation"""
    scanner = Scanner()
    
    # Create sample data
    n_samples = 50
    dates = pd.date_range(end=datetime.now(), periods=n_samples, freq='min')
    
    # Create a series that goes up and down to test RSI
    prices = [50000 + i*100 if i < 25 else 50000 + (50-i)*100 for i in range(n_samples)]
    
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p + 50 for p in prices],
        'low': [p - 50 for p in prices],
        'close': prices,
        'volume': [1000] * n_samples
    })
    
    # Calculate RSI
    result = scanner.calculate_rsi(data)
    
    # Check that RSI column exists
    assert 'rsi' in result.columns
    assert len(result) == len(data)
    
    # Check that RSI values are within valid range (0-100)
    rsi_values = result['rsi'].dropna()
    assert all(0 <= rsi <= 100 for rsi in rsi_values)


@pytest.mark.asyncio
async def test_calculate_supertrend():
    """Test Supertrend calculation"""
    scanner = Scanner()
    
    # Create sample data
    n_samples = 30
    dates = pd.date_range(end=datetime.now(), periods=n_samples, freq='min')
    
    # Create realistic price data
    np.random.seed(42)  # For reproducible results
    prices = 50000 + np.random.randn(n_samples).cumsum() * 100
    
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices + np.random.randn(n_samples) * 20,
        'high': prices + np.abs(np.random.randn(n_samples)) * 50,
        'low': prices - np.abs(np.random.randn(n_samples)) * 50,
        'close': prices,
        'volume': [1000] * n_samples
    })
    
    # Calculate Supertrend
    result = scanner.calculate_supertrend(data)
    
    # Check that Supertrend columns exist
    assert 'supertrend' in result.columns
    assert 'direction' in result.columns
    assert len(result) == len(data)


@pytest.mark.asyncio
async def test_calculate_ma():
    """Test Moving Average calculation"""
    scanner = Scanner()
    
    # Create sample data
    n_samples = 30
    dates = pd.date_range(end=datetime.now(), periods=n_samples, freq='min')
    
    prices = 50000 + np.arange(n_samples) * 100  # Increasing prices
    
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p + 50 for p in prices],
        'low': [p - 50 for p in prices],
        'close': prices,
        'volume': [1000] * n_samples
    })
    
    # Calculate MA
    result = scanner.calculate_ma(data)
    
    # Check that MA column exists
    assert 'ma' in result.columns
    assert len(result) == len(data)


@pytest.mark.asyncio
async def test_detect_trend_change():
    """Test trend change detection"""
    scanner = Scanner()
    
    # Create sample data with direction column
    n_samples = 10
    dates = pd.date_range(end=datetime.now(), periods=n_samples, freq='min')
    
    prices = 50000 + np.arange(n_samples) * 100
    
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p + 50 for p in prices],
        'low': [p - 50 for p in prices],
        'close': prices,
        'volume': [1000] * n_samples,
        'direction': [1, 1, 1, 1, 1, 1, 1, 1, 1, -1]  # Change from 1 to -1 in last two (index 8 to 9)
    })
    
    # Test trend change detection
    trend_change = scanner.detect_trend_change(data)
    assert trend_change is True  # Should detect change from index 4 to 5


@pytest.mark.asyncio
async def test_get_signal():
    """Test signal generation"""
    scanner = Scanner()
    
    # Create sample data with indicators
    n_samples = 10
    dates = pd.date_range(end=datetime.now(), periods=n_samples, freq='min')
    
    prices = 50000 + np.arange(n_samples) * 100
    
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p + 50 for p in prices],
        'low': [p - 50 for p in prices],
        'close': prices,
        'volume': [1000] * n_samples,
        'direction': [1] * n_samples,  # Uptrend
        'rsi': [40] * n_samples,      # Not overbought
        'ma': [prices[0] - 100] * n_samples  # Price above MA
    })
    
    # Test signal generation
    signal = scanner.get_signal(data)
    # With uptrend, not overbought RSI, and price above MA, should be positive (BUY)
    assert isinstance(signal, (int, float))
    assert -1.0 <= signal <= 1.0
    
    # Test signal_to_string conversion
    assert scanner.signal_to_string(0.5) == "BUY"
    assert scanner.signal_to_string(-0.5) == "SELL"
    assert scanner.signal_to_string(0.0) == "HOLD"


@pytest.mark.asyncio
async def test_scan_market(scanner):
    """Test market scanning functionality"""
    # Run a quick scan
    results = await scanner.scan_market()
    
    # Check that results contain expected structure
    assert isinstance(results, dict)
    assert len(results) > 0
    
    # Check that results are structured by pair and timeframe
    for pair, timeframes in results.items():
        assert isinstance(timeframes, dict)
        for timeframe, data in timeframes.items():
            assert isinstance(data, dict)
            assert 'signal' in data


@pytest.mark.asyncio
async def test_get_latest_signals(scanner):
    """Test getting latest signals"""
    # Run a scan first to populate the database
    await scanner.scan_market()
    
    # Get latest signals
    signals = await scanner.get_latest_signals()
    
    # Check that signals are returned for all configured pairs
    config = get_config()
    pairs = config["pairs"]
    
    assert isinstance(signals, dict)
    assert len(signals) == len(pairs)
    
    for pair in pairs:
        assert pair in signals
        assert signals[pair] in ["BUY", "SELL", "HOLD"]