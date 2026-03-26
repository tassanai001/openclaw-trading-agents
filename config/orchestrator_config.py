"""
Orchestrator Configuration
Defines settings for the main orchestrator including agent order, timeouts, and retry logic.
"""

# Agent execution order
AGENT_ORDER = ["scanner", "sentiment", "strategy", "risk", "execution", "learning"]

# Timeout settings (in seconds)
AGENT_TIMEOUTS = {
    "data_collector": 30,
    "market_analyzer": 45,
    "risk_manager": 30,
    "strategy_generator": 60,
    "trade_executor": 45,
    "performance_tracker": 30
}

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Trading cycle settings
TRADING_CYCLE_INTERVAL = 300  # seconds (5 minutes)
ENABLE_LOGGING = True
LOG_TO_DATABASE = True
LOG_TO_MARKDOWN = True