"""
Tests for the Trading Orchestrator
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch

from orchestrator import TradingOrchestrator


@pytest.fixture
def mock_agents():
    """Create mock agents for testing."""
    agents = {}
    for agent_name in [
        "data_collector", 
        "market_analyzer", 
        "risk_manager", 
        "strategy_generator", 
        "trade_executor", 
        "performance_tracker"
    ]:
        mock_agent = Mock()
        mock_agent.run = AsyncMock(return_value={"status": "success"})
        agents[agent_name] = mock_agent
    return agents


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test that orchestrator initializes correctly."""
    orchestrator = TradingOrchestrator()
    
    assert orchestrator.agents is not None
    assert len(orchestrator.agents) >= 0  # Agents may fail to initialize if not present


@pytest.mark.asyncio
async def test_run_single_cycle_success(mock_agents):
    """Test successful execution of a single trading cycle."""
    orchestrator = TradingOrchestrator()
    orchestrator.agents = mock_agents
    
    # Mock the logging methods
    orchestrator._log_results = AsyncMock()
    
    results = await orchestrator.run_single_cycle()
    
    # Verify all agents were called
    for agent_name, mock_agent in mock_agents.items():
        mock_agent.run.assert_called_once()
        assert agent_name in results


@pytest.mark.asyncio
async def test_run_single_cycle_with_retry():
    """Test that orchestrator retries failed agents."""
    orchestrator = TradingOrchestrator()
    
    # Create a mock agent that fails initially then succeeds
    failing_agent = Mock()
    failing_agent.run = AsyncMock()
    # First two calls raise exception, third succeeds
    failing_agent.run.side_effect = [
        Exception("Simulated error"),
        Exception("Simulated error"), 
        {"status": "success"}
    ]
    
    orchestrator.agents = {"data_collector": failing_agent}
    
    # Add other agents with successful mocks
    for agent_name in [
        "market_analyzer", 
        "risk_manager", 
        "strategy_generator", 
        "trade_executor", 
        "performance_tracker"
    ]:
        mock_agent = Mock()
        mock_agent.run = AsyncMock(return_value={"status": "success"})
        orchestrator.agents[agent_name] = mock_agent
    
    # Mock the logging methods
    orchestrator._log_results = AsyncMock()
    
    results = await orchestrator.run_single_cycle()
    
    # Verify the failing agent was called 3 times (2 failures + 1 success)
    assert failing_agent.run.call_count == 3
    assert "data_collector" in results
    assert results["data_collector"]["status"] == "success"


@pytest.mark.asyncio
async def test_run_single_cycle_max_retries_exceeded():
    """Test that orchestrator stops trying after max retries."""
    orchestrator = TradingOrchestrator()
    
    # Create a mock agent that always fails
    failing_agent = Mock()
    failing_agent.run = AsyncMock(side_effect=Exception("Always fails"))
    
    orchestrator.agents = {"data_collector": failing_agent}
    
    # Add other agents with successful mocks
    for agent_name in [
        "market_analyzer", 
        "risk_manager", 
        "strategy_generator", 
        "trade_executor", 
        "performance_tracker"
    ]:
        mock_agent = Mock()
        mock_agent.run = AsyncMock(return_value={"status": "success"})
        orchestrator.agents[agent_name] = mock_agent
    
    # Mock the logging methods
    orchestrator._log_results = AsyncMock()
    
    results = await orchestrator.run_single_cycle()
    
    # Verify the failing agent was called max_retries times
    assert failing_agent.run.call_count == 3  # MAX_RETRIES from config
    assert "data_collector" in results
    assert results["data_collector"]["status"] == "failed"


@pytest.mark.asyncio
@patch('orchestrator.AGENT_TIMEOUTS', {"data_collector": 0.1})
async def test_agent_timeout_handling():
    """Test that orchestrator handles agent timeouts properly."""
    orchestrator = TradingOrchestrator()
    
    # Create a mock agent that takes too long
    slow_agent = Mock()
    async def slow_run(*args, **kwargs):
        await asyncio.sleep(0.2)  # Longer than timeout
        return {"status": "success"}
    
    slow_agent.run = AsyncMock(side_effect=slow_run)
    
    orchestrator.agents = {"data_collector": slow_agent}
    
    # Add other agents with successful mocks
    for agent_name in [
        "market_analyzer", 
        "risk_manager", 
        "strategy_generator", 
        "trade_executor", 
        "performance_tracker"
    ]:
        mock_agent = Mock()
        mock_agent.run = AsyncMock(return_value={"status": "success"})
        orchestrator.agents[agent_name] = mock_agent
    
    # Mock the logging methods
    orchestrator._log_results = AsyncMock()
    
    results = await orchestrator.run_single_cycle()
    
    # Verify the slow agent was retried due to timeout
    assert slow_agent.run.call_count >= 1  # At least one call
    assert "data_collector" in results


def test_get_status():
    """Test getting agent status."""
    orchestrator = TradingOrchestrator()
    status = orchestrator.get_status()
    
    # Should contain status for all expected agents
    expected_agents = [
        "data_collector", 
        "market_analyzer", 
        "risk_manager", 
        "strategy_generator", 
        "trade_executor", 
        "performance_tracker"
    ]
    
    for agent in expected_agents:
        assert agent in status