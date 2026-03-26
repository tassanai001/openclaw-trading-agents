"""
Risk Agent module for managing trading risks
Implements position sizing (2%), daily loss limit (5%), max positions (5)
"""
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from .config import RiskConfig

logger = logging.getLogger(__name__)


class RiskAgent:
    """
    Risk management agent that enforces trading limits and constraints.
    Implements position sizing (2%), daily loss limit (5%), max positions (5).
    """
    
    def __init__(self, initial_account_value: float = 100000.0):
        """
        Initialize the Risk Agent
        
        Args:
            initial_account_value: Starting account value for risk calculations
        """
        self.config = RiskConfig()
        self.initial_account_value = initial_account_value
        self.current_account_value = initial_account_value
        self.daily_pnl = 0.0
        self.positions_count = 0
        self.today = datetime.now().date()
        
        logger.info(f"Risk Agent initialized with account value: ${initial_account_value:,.2f}")
    
    def check_position_size(self, position_value: float, account_value: Optional[float] = None) -> Tuple[bool, str]:
        """
        Check if a proposed position size is within limits (2% of account)
        
        Args:
            position_value: Proposed position value
            account_value: Current account value (uses internal value if None)
            
        Returns:
            Tuple of (is_valid, reason)
        """
        current_value = account_value or self.current_account_value
        max_position_size = current_value * self.config.position_size_limit
        
        if abs(position_value) > max_position_size:
            reason = f"Position size ${abs(position_value):,.2f} exceeds 2% limit (${max_position_size:,.2f})"
            logger.warning(reason)
            return False, reason
            
        return True, "Position size within limits"
    
    def check_daily_loss_limit(self, pnl_change: float, account_value: Optional[float] = None) -> Tuple[bool, str]:
        """
        Check if a trade would exceed the daily loss limit (5% of account)
        
        Args:
            pnl_change: Expected P&L change from the trade
            account_value: Current account value (uses internal value if None)
            
        Returns:
            Tuple of (is_valid, reason)
        """
        current_value = account_value or self.current_account_value
        max_daily_loss = current_value * self.config.daily_loss_limit
        
        # Check if we're adding to losses or if this trade alone would exceed the limit
        potential_daily_pnl = self.daily_pnl + pnl_change
        if potential_daily_pnl < -max_daily_loss:
            reason = f"This trade would exceed daily loss limit of {self.config.daily_loss_limit*100}% " \
                     f"(${max_daily_loss:,.2f} loss)"
            logger.warning(reason)
            return False, reason
            
        return True, "Daily loss limit check passed"
    
    def check_max_positions(self, new_positions: int = 1) -> Tuple[bool, str]:
        """
        Check if opening new positions would exceed the maximum allowed positions (5)
        
        Args:
            new_positions: Number of new positions to open
            
        Returns:
            Tuple of (is_valid, reason)
        """
        total_positions = self.positions_count + new_positions
        if total_positions > self.config.max_positions:
            reason = f"Opening {new_positions} new position(s) would exceed maximum of " \
                     f"{self.config.max_positions} positions (currently: {self.positions_count})"
            logger.warning(reason)
            return False, reason
            
        return True, "Max positions check passed"
    
    def validate_trade(self, position_value: float, pnl_change: float = 0.0, 
                      new_positions: int = 0) -> Tuple[bool, str]:
        """
        Validate a trade against all risk constraints
        
        Args:
            position_value: Value of the proposed position
            pnl_change: Expected P&L impact of the trade
            new_positions: Number of new positions this trade represents
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check position size
        is_valid, reason = self.check_position_size(position_value)
        if not is_valid:
            return False, reason
        
        # Check daily loss limit
        is_valid, reason = self.check_daily_loss_limit(pnl_change)
        if not is_valid:
            return False, reason
        
        # Check max positions
        is_valid, reason = self.check_max_positions(new_positions)
        if not is_valid:
            return False, reason
        
        return True, "Trade passes all risk checks"
    
    def update_account_value(self, new_value: float):
        """
        Update the current account value
        
        Args:
            new_value: New account value
        """
        self.current_account_value = new_value
        logger.debug(f"Account value updated to: ${new_value:,.2f}")
    
    def update_daily_pnl(self, pnl_change: float):
        """
        Update the daily P&L with a new change
        
        Args:
            pnl_change: Change in daily P&L
        """
        # Reset daily P&L if date has changed
        today = datetime.now().date()
        if today != self.today:
            self.daily_pnl = 0.0
            self.today = today
            logger.info("New trading day, resetting daily P&L")
        
        self.daily_pnl += pnl_change
        logger.debug(f"Daily P&L updated to: ${self.daily_pnl:,.2f}")
    
    def update_positions_count(self, change: int):
        """
        Update the count of current positions
        
        Args:
            change: Change in position count (+1 for opening, -1 for closing)
        """
        old_count = self.positions_count
        self.positions_count = max(0, self.positions_count + change)
        logger.debug(f"Positions count updated from {old_count} to {self.positions_count}")
    
    def get_risk_status(self) -> Dict:
        """
        Get current risk status
        
        Returns:
            Dictionary with current risk metrics
        """
        return {
            'account_value': self.current_account_value,
            'daily_pnl': self.daily_pnl,
            'positions_count': self.positions_count,
            'max_daily_loss': self.current_account_value * self.config.daily_loss_limit,
            'max_position_size': self.current_account_value * self.config.position_size_limit,
            'max_positions': self.config.max_positions,
            'remaining_daily_loss': (self.current_account_value * self.config.daily_loss_limit) - abs(self.daily_pnl),
            'remaining_positions': self.config.max_positions - self.positions_count
        }