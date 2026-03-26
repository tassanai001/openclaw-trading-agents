"""
Tests for Execution Agent
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from agents.execution import ExecutionAgent, ExecutionConfig


@pytest.fixture
def execution_config():
    """Fixture for execution configuration with mock mode enabled"""
    return ExecutionConfig(
        api_key="test_api_key",
        secret="test_secret",
        mock_mode=True,
        is_testnet=True
    )


@pytest.mark.asyncio
async def test_execution_agent_initialization(execution_config):
    """Test that Execution Agent initializes correctly"""
    agent = ExecutionAgent(execution_config)
    await agent.initialize()
    
    assert agent.config == execution_config
    assert agent.api.mock_mode is True
    assert agent.api.is_testnet is True


@pytest.mark.asyncio
async def test_place_limit_order(execution_config):
    """Test placing a limit order"""
    agent = ExecutionAgent(execution_config)
    await agent.initialize()
    
    # Place a limit order
    result = await agent.place_order(
        asset="BTCUSD",
        side="B",
        leverage=10,
        order_type="limit",
        price=40000.0,
        size=0.1
    )
    
    # Since we're in mock mode, the order should succeed
    assert result.success is True
    assert result.order_id is not None
    assert "mock_" in result.order_id


@pytest.mark.asyncio
async def test_place_market_order(execution_config):
    """Test placing a market order"""
    agent = ExecutionAgent(execution_config)
    await agent.initialize()
    
    # Place a market order
    result = await agent.place_order(
        asset="BTCUSD",
        side="S",
        leverage=5,
        order_type="market",
        size=0.05
    )
    
    # Since we're in mock mode, the order should succeed
    assert result.success is True
    assert result.order_id is not None
    assert "mock_" in result.order_id


@pytest.mark.asyncio
async def test_cancel_order(execution_config):
    """Test canceling an order"""
    agent = ExecutionAgent(execution_config)
    await agent.initialize()
    
    # Cancel an order (in mock mode, this should succeed)
    result = await agent.cancel_order("test_order_id_123")
    
    assert result is True


@pytest.mark.asyncio
async def test_get_open_orders(execution_config):
    """Test getting open orders"""
    agent = ExecutionAgent(execution_config)
    await agent.initialize()
    
    # Get open orders (in mock mode)
    result = await agent.get_open_orders()
    
    assert "open_orders" in result
    assert isinstance(result["open_orders"], list)


@pytest.mark.asyncio
async def test_get_account_info(execution_config):
    """Test getting account information"""
    agent = ExecutionAgent(execution_config)
    await agent.initialize()
    
    # Get account info (in mock mode)
    result = await agent.get_account_info()
    
    assert "account_value" in result or "error" not in result


@pytest.mark.asyncio
async def test_invalid_limit_order_without_price(execution_config):
    """Test that placing a limit order without price raises an error"""
    agent = ExecutionAgent(execution_config)
    await agent.initialize()
    
    # Attempt to place a limit order without price
    result = await agent.place_order(
        asset="BTCUSD",
        side="B",
        leverage=10,
        order_type="limit",
        size=0.1
        # Missing price parameter
    )
    
    # Should fail because price is required for limit orders
    assert result.success is False
    assert "Price must be specified for limit orders" in result.error


if __name__ == "__main__":
    pytest.main([__file__])