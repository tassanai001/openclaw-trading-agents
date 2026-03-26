"""
Strategy Agent that combines Scanner and Sentiment signals.
Makes LONG/SHORT/WAIT decisions based on weighted signals.
"""

import numpy as np
from enum import Enum
from typing import Dict, Any, Optional
from .config import STRATEGY_CONFIG


class TradeDecision(Enum):
    """Possible trading decisions."""
    LONG = "LONG"
    SHORT = "SHORT"
    WAIT = "WAIT"


class StrategyAgent:
    """Strategy Agent that combines scanner and sentiment signals to make trading decisions."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Strategy Agent.
        
        Args:
            config: Configuration dictionary, defaults to STRATEGY_CONFIG
        """
        self.config = config or STRATEGY_CONFIG
        
    def combine_signals(self, scanner_signal: float, sentiment_signal: float) -> float:
        """
        Combine scanner and sentiment signals based on configured weights.
        
        Args:
            scanner_signal: Signal from scanner (typically -1 to 1)
            sentiment_signal: Signal from sentiment analysis (typically -1 to 1)
            
        Returns:
            Combined signal value
        """
        scanner_weight = self.config['signal_weights']['scanner']
        sentiment_weight = self.config['signal_weights']['sentiment']
        
        combined_signal = (
            scanner_signal * scanner_weight +
            sentiment_signal * sentiment_weight
        )
        
        return combined_signal
    
    def check_circuit_breaker(self, fng_value: int = None) -> Dict[str, bool]:
        """Check if circuit breakers should halt trading"""
        breakers = {'halt_trading': False, 'reason': None, 'severity': 'none'}
        
        if fng_value is not None and fng_value < 20:
            breakers['halt_trading'] = True
            breakers['reason'] = f'Extreme Fear (F&G: {fng_value})'
            breakers['severity'] = 'high'
        elif fng_value is not None and fng_value > 80:
            breakers['halt_trading'] = True
            breakers['reason'] = f'Extreme Greed (F&G: {fng_value})'
            breakers['severity'] = 'medium'
        
        return breakers
    
    def make_decision(self, scanner_signal: float, sentiment_signal: float, fng_value: int = None) -> Dict[str, Any]:
        """
        Make a trading decision based on combined signals.
        
        Args:
            scanner_signal: Signal from scanner (typically -1 to 1)
            sentiment_signal: Signal from sentiment analysis (typically -1 to 1)
            fng_value: Optional Fear & Greed Index value for circuit breaker
            
        Returns:
            Dictionary containing decision and metadata
        """
        # Check circuit breaker first
        circuit_breaker = self.check_circuit_breaker(fng_value)
        if circuit_breaker['halt_trading']:
            return {
                'decision': TradeDecision.WAIT.value,
                'combined_signal': 0.0,
                'position_size': 0.0,
                'circuit_breaker': circuit_breaker,
                'signals': {
                    'scanner': scanner_signal,
                    'sentiment': sentiment_signal,
                    'weights': self.config['signal_weights']
                }
            }
        
        combined_signal = self.combine_signals(scanner_signal, sentiment_signal)
        
        # Determine decision based on thresholds
        long_threshold = self.config['decision_thresholds']['long_min']
        short_threshold = self.config['decision_thresholds']['short_min']
        
        if combined_signal >= long_threshold:
            decision = TradeDecision.LONG
        elif combined_signal <= -short_threshold:
            decision = TradeDecision.SHORT
        else:
            decision = TradeDecision.WAIT
        
        # Calculate position size based on signal strength
        position_size = self.calculate_position_size(abs(combined_signal))
        
        return {
            'decision': decision.value,
            'combined_signal': combined_signal,
            'position_size': position_size,
            'signals': {
                'scanner': scanner_signal,
                'sentiment': sentiment_signal,
                'weights': self.config['signal_weights']
            }
        }
    
    def calculate_position_size(self, signal_strength: float) -> float:
        """
        Calculate position size based on signal strength.
        
        Args:
            signal_strength: Absolute value of combined signal
            
        Returns:
            Position size as percentage of portfolio (0 to max_allocation)
        """
        base_allocation = self.config['position_sizing']['default_allocation']
        max_allocation = self.config['position_sizing']['max_allocation']
        
        # Scale position size with signal strength, capped at max allocation
        position_size = min(base_allocation * (signal_strength * 10), max_allocation)
        
        # Ensure minimum position size when we have a signal
        if signal_strength > 0.05:  # Small threshold to ensure we have a meaningful signal
            position_size = max(position_size, base_allocation * 0.2)
        
        return round(position_size, 4)
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        Update the agent configuration.
        
        Args:
            new_config: New configuration dictionary
        """
        self.config.update(new_config)