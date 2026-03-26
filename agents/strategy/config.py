"""
Configuration for Strategy Agent.
"""

STRATEGY_CONFIG = {
    'signal_weights': {
        'scanner': 0.6,  # 60% weight to scanner signals
        'sentiment': 0.4  # 40% weight to sentiment signals
    },
    'decision_thresholds': {
        'long_min': 0.1,
        'short_min': 0.1,
    },
    'position_sizing': {
        'default_allocation': 0.02,  # 2% of portfolio by default (risk-compliant)
        'max_allocation': 0.05,    # Maximum 5% allocation (within risk limits)
    }
}