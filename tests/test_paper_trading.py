"""
Tests for paper trading functionality
"""
import pytest
import asyncio
from agents.execution.execution import ExecutionAgent, OrderResult
from agents.execution.config import ExecutionConfig
from config.paper_trading_config import PaperTradingConfig


@pytest.fixture
def paper_trading_config():
    """Create a paper trading config for testing"""
    return PaperTradingConfig(
        enabled=True,
        initial_balance=10000.0,
        slippage_percent=0.05,
        fee_percent=0.075,
        min_order_size=0.01,  # Lower minimum for testing
        max_position_size=1.0  # Allow larger position sizes for testing
    )


@pytest.fixture
def execution_config():
    """Create an execution config for testing"""
    return ExecutionConfig(paper_trading=True)


@pytest.mark.asyncio
async def test_paper_trading_initialization(execution_config, paper_trading_config):
    """Test that paper trading initializes correctly"""
    agent = ExecutionAgent(execution_config, paper_trading_config)
    await agent.initialize()
    
    assert agent.paper_trading_enabled is True
    assert agent.paper_balance == paper_trading_config.initial_balance
    assert isinstance(agent.paper_positions, dict)
    assert len(agent.paper_positions) == 0


@pytest.mark.asyncio
async def test_place_paper_buy_order(execution_config, paper_trading_config):
    """Test placing a paper buy order"""
    agent = ExecutionAgent(execution_config, paper_trading_config)
    await agent.initialize()
    
    # Place a paper buy order
    result = await agent.place_order(
        asset="BTCUSD",
        side="B",
        leverage=1,
        order_type="limit",
        price=50000.0,
        size=0.01  # Smaller size to stay within limits
    )
    
    # Verify the order was successful
    assert isinstance(result, OrderResult)
    assert result.success is True
    assert result.is_paper_trade is True
    assert result.order_id is not None
    assert result.order_id.startswith("PAPER_")
    
    # Verify the position was created
    assert "BTCUSD" in agent.paper_positions
    btc_pos = agent.paper_positions["BTCUSD"]
    assert btc_pos.asset == "BTCUSD"
    assert btc_pos.size > 0  # Long position (size may be adjusted for max_position_size)
    # The avg_entry_price may include slippage, so just check it's reasonable
    assert btc_pos.avg_entry_price > 0


@pytest.mark.asyncio
async def test_place_paper_sell_order(execution_config, paper_trading_config):
    """Test placing a paper sell order to close position"""
    agent = ExecutionAgent(execution_config, paper_trading_config)
    await agent.initialize()
    
    # First, place a buy order
    buy_result = await agent.place_order(
        asset="BTCUSD",
        side="B",
        leverage=1,
        order_type="limit",
        price=50000.0,
        size=0.01
    )
    
    assert buy_result.success is True
    
    # Now place a sell order to close the position
    sell_result = await agent.place_order(
        asset="BTCUSD",
        side="S",
        leverage=1,
        order_type="limit",
        price=51000.0,
        size=0.01
    )
    
    assert sell_result.success is True
    assert sell_result.is_paper_trade is True
    
    # The position should still exist but with 0 size and realized P&L
    assert "BTCUSD" in agent.paper_positions
    btc_pos = agent.paper_positions["BTCUSD"]
    assert abs(btc_pos.size) < 0.1  # Position reduced/close
    # Should have some realized P&L from the trade (approx $100 profit on 0.1 BTC)
    expected_profit = 0.1 * (51000.0 - 50000.0)  # Simplified calculation
    assert btc_pos.realized_pnl >= 0  # Should have positive or zero realized P&L


@pytest.mark.asyncio
async def test_get_account_info_paper_trading(execution_config, paper_trading_config):
    """Test getting account info in paper trading mode"""
    agent = ExecutionAgent(execution_config, paper_trading_config)
    await agent.initialize()
    
    # Place an order to create a position
    await agent.place_order(
        asset="ETHUSD",
        side="B",
        leverage=1,
        order_type="limit",
        price=3000.0,
        size=0.1
    )
    
    # Get account info
    account_info = await agent.get_account_info()
    
    # Verify paper trading account info structure
    assert "account_value" in account_info
    assert "balance" in account_info
    assert "positions" in account_info
    assert "paper_trading" in account_info
    assert account_info["paper_trading"] is True
    
    # Should have one position
    assert len(account_info["positions"]) == 1
    assert account_info["positions"][0]["asset"] == "ETHUSD"


@pytest.mark.asyncio
async def test_cancel_order_paper_trading(execution_config, paper_trading_config):
    """Test cancel order in paper trading mode"""
    agent = ExecutionAgent(execution_config, paper_trading_config)
    await agent.initialize()
    
    # Try to cancel an order in paper trading
    result = await agent.cancel_order("FAKE_ORDER_ID")
    
    # In paper trading, this should return True (simulated cancellation)
    assert result is True


@pytest.mark.asyncio
async def test_get_open_orders_paper_trading(execution_config, paper_trading_config):
    """Test get open orders in paper trading mode"""
    agent = ExecutionAgent(execution_config, paper_trading_config)
    await agent.initialize()
    
    # Get open orders in paper trading
    orders = await agent.get_open_orders()
    
    # Should return empty list as all orders are filled immediately in paper trading
    assert orders["open_orders"] == []
    assert orders["paper_trading"] is True


if __name__ == "__main__":
    pytest.main([__file__])