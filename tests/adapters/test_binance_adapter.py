"""
Tests for Binance Adapter

Note: These tests require valid Binance Testnet credentials.
Get them from: https://testnet.binance.vision/
"""
import pytest
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agents.execution.adapters.binance import BinanceAdapter
from agents.execution.adapters.hyperliquid import HyperliquidAdapter
from agents.execution.models.common import ExchangeCredentials, OrderSide, OrderType
from agents.execution.models.order import Order, OrderResult


@pytest.fixture
def binance_credentials():
    """Get Binance credentials from environment"""
    return ExchangeCredentials(
        api_key=os.getenv("BINANCE_API_KEY", ""),
        api_secret=os.getenv("BINANCE_API_SECRET", ""),
        testnet=os.getenv("BINANCE_TESTNET", "true").lower() == "true"
    )


@pytest.fixture
def binance_adapter(binance_credentials):
    """Create Binance adapter instance"""
    return BinanceAdapter(binance_credentials)


@pytest.mark.asyncio
async def test_initialize(binance_adapter):
    """Test adapter initialization"""
    success = await binance_adapter.initialize()
    assert success is True, "Failed to initialize Binance adapter"
    assert binance_adapter._initialized is True
    assert binance_adapter.client is not None
    
    # Cleanup
    await binance_adapter.close()


@pytest.mark.asyncio
async def test_get_balance(binance_adapter):
    """Test getting account balance"""
    initialized = await binance_adapter.initialize()
    if not initialized:
        pytest.skip("Binance adapter not initialized (no credentials)")
    
    balance = await binance_adapter.get_balance()
    
    assert balance is not None
    assert balance.currency == "USDT"
    assert balance.total_balance >= 0
    assert balance.available_balance >= 0
    assert balance.locked_balance >= 0
    
    print(f"Balance: {balance.total_balance} {balance.currency}")
    print(f"Available: {balance.available_balance}")
    print(f"Locked: {balance.locked_balance}")
    
    # Cleanup
    await binance_adapter.close()


@pytest.mark.asyncio
async def test_get_ticker_price(binance_adapter):
    """Test getting ticker price"""
    initialized = await binance_adapter.initialize()
    if not initialized:
        pytest.skip("Binance adapter not initialized (no credentials)")
    
    # Test BTC/USDT
    price = await binance_adapter.get_ticker_price("BTCUSDT")
    assert price > 0, "BTC price should be > 0"
    print(f"BTC/USDT Price: ${price:.2f}")
    
    # Test ETH/USDT
    eth_price = await binance_adapter.get_ticker_price("ETHUSDT")
    assert eth_price > 0, "ETH price should be > 0"
    print(f"ETH/USDT Price: ${eth_price:.2f}")
    
    # Cleanup
    await binance_adapter.close()


@pytest.mark.asyncio
async def test_get_symbol_info(binance_adapter):
    """Test getting symbol info"""
    # No initialization needed for this method
    info = binance_adapter.get_symbol_info("BTCUSDT")
    
    assert "base_asset_precision" in info
    assert "quote_precision" in info
    assert "base_asset_step_size" in info
    assert "min_quantity" in info
    assert "min_notional" in info
    
    print(f"Symbol Info: {info}")


@pytest.mark.asyncio
async def test_place_order_small(binance_adapter):
    """Test placing a small order (market buy)"""
    initialized = await binance_adapter.initialize()
    if not initialized:
        pytest.skip("Binance adapter not initialized (no credentials)")
    
    # Create a small test order (minimum ~$10 on Binance)
    order = Order(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        type=OrderType.MARKET,
        quantity=0.0002  # Very small amount for testing
    )
    
    print(f"Placing test order: {order}")
    
    result = await binance_adapter.place_order(order)
    
    # Order should either succeed or fail with a clear error
    assert isinstance(result, OrderResult)
    
    if result.success:
        assert result.order_id is not None
        print(f"✅ Order placed successfully: {result.order_id}")
        print(f"Filled: {result.filled_quantity} @ {result.filled_price}")
        print(f"Fee: {result.fee} {result.fee_currency}")
    else:
        print(f"❌ Order failed: {result.message}")
    
    # Cleanup
    await binance_adapter.close()


@pytest.mark.asyncio
async def test_get_open_orders(binance_adapter):
    """Test getting open orders"""
    initialized = await binance_adapter.initialize()
    if not initialized:
        pytest.skip("Binance adapter not initialized (no credentials)")
    
    orders = await binance_adapter.get_open_orders()
    
    assert isinstance(orders, list)
    print(f"Open orders: {len(orders)}")
    
    for order in orders:
        print(f"  - {order.side.value} {order.quantity} {order.symbol} @ {order.price}")
    
    # Cleanup
    await binance_adapter.close()


@pytest.mark.asyncio
async def test_get_positions(binance_adapter):
    """Test getting positions"""
    initialized = await binance_adapter.initialize()
    if not initialized:
        pytest.skip("Binance adapter not initialized (no credentials)")
    
    positions = await binance_adapter.get_positions()
    
    assert isinstance(positions, list)
    print(f"Positions: {len(positions)}")
    
    for pos in positions:
        print(f"  - {pos.symbol}: {pos.quantity} @ ${pos.current_price:.2f}")
        print(f"    Value: ${pos.market_value:.2f}")
    
    # Cleanup
    await binance_adapter.close()


@pytest.mark.asyncio
async def test_adapter_name(binance_adapter):
    """Test adapter name property"""
    assert binance_adapter.name == "Binance"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
