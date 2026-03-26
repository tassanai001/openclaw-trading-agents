"""
Tests for Hyperliquid Adapter
"""
import pytest
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agents.execution.adapters.hyperliquid import HyperliquidAdapter
from agents.execution.models.common import ExchangeCredentials, OrderSide, OrderType
from agents.execution.models.order import Order, OrderResult


@pytest.fixture
def hyperliquid_credentials():
    """Get Hyperliquid credentials from environment"""
    return ExchangeCredentials(
        api_key=os.getenv("HYPERLIQUID_API_KEY", ""),
        api_secret=os.getenv("HYPERLIQUID_API_SECRET", ""),
        testnet=True
    )


@pytest.fixture
def hyperliquid_adapter(hyperliquid_credentials):
    """Create Hyperliquid adapter instance"""
    return HyperliquidAdapter(hyperliquid_credentials)


@pytest.mark.asyncio
async def test_initialize(hyperliquid_adapter):
    """Test adapter initialization"""
    success = await hyperliquid_adapter.initialize()
    assert success is True, "Failed to initialize Hyperliquid adapter"
    assert hyperliquid_adapter._initialized is True
    assert hyperliquid_adapter.api is not None
    
    # Cleanup
    await hyperliquid_adapter.close()


@pytest.mark.asyncio
async def test_get_balance(hyperliquid_adapter):
    """Test getting account balance"""
    initialized = await hyperliquid_adapter.initialize()
    if not initialized:
        pytest.skip("Hyperliquid adapter not initialized (no credentials)")
    
    balance = await hyperliquid_adapter.get_balance()
    
    assert balance is not None
    assert balance.currency == "USDT"
    assert balance.total_balance >= 0
    
    print(f"Balance: {balance.total_balance} {balance.currency}")
    print(f"Available: {balance.available_balance}")
    
    # Cleanup
    await hyperliquid_adapter.close()


@pytest.mark.asyncio
async def test_get_ticker_price(hyperliquid_adapter):
    """Test getting ticker price"""
    initialized = await hyperliquid_adapter.initialize()
    if not initialized:
        pytest.skip("Hyperliquid adapter not initialized (no credentials)")
    
    # Test BTC/USDT
    price = await hyperliquid_adapter.get_ticker_price("BTCUSDT")
    assert price > 0, "BTC price should be > 0"
    print(f"BTC/USDT Price: ${price:.2f}")
    
    # Cleanup
    await hyperliquid_adapter.close()


@pytest.mark.asyncio
async def test_get_symbol_info(hyperliquid_adapter):
    """Test getting symbol info"""
    info = hyperliquid_adapter.get_symbol_info("BTCUSDT")
    
    assert "base_asset_precision" in info
    assert "quote_precision" in info
    assert "base_asset_step_size" in info
    assert "min_quantity" in info
    
    print(f"Symbol Info: {info}")


@pytest.mark.asyncio
async def test_adapter_name(hyperliquid_adapter):
    """Test adapter name property"""
    assert hyperliquid_adapter.name == "Hyperliquid"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
