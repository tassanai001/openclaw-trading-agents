"""
Configuration for Risk Agent
"""

RISK_CONFIG = {
    # Position sizing: maximum 2% of account per position
    'POSITION_SIZE_LIMIT': 0.02,
    
    # Daily loss limit: maximum 5% loss per day
    'DAILY_LOSS_LIMIT': 0.05,
    
    # Maximum number of positions allowed
    'MAX_POSITIONS': 5,
    
    # Risk per trade as percentage of account
    'RISK_PER_TRADE': 0.02,
}

class RiskConfig:
    """Risk configuration class"""
    
    def __init__(self):
        self.position_size_limit = RISK_CONFIG['POSITION_SIZE_LIMIT']
        self.daily_loss_limit = RISK_CONFIG['DAILY_LOSS_LIMIT']
        self.max_positions = RISK_CONFIG['MAX_POSITIONS']
        self.risk_per_trade = RISK_CONFIG['RISK_PER_TRADE']