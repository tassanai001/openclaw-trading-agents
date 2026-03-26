"""
Tests for Strategy Agent.
"""

import unittest
from agents.strategy.strategy import StrategyAgent, TradeDecision
from agents.strategy.config import STRATEGY_CONFIG


class TestStrategyAgent(unittest.TestCase):
    """Test cases for StrategyAgent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = StrategyAgent()
    
    def test_combine_signals_equal_weights(self):
        """Test combining signals with equal positive values."""
        scanner_signal = 0.5
        sentiment_signal = 0.5
        
        result = self.agent.combine_signals(scanner_signal, sentiment_signal)
        expected = (0.5 * 0.6) + (0.5 * 0.4)  # 60/40 weights
        self.assertEqual(result, expected)
    
    def test_combine_signals_mixed_signs(self):
        """Test combining signals with mixed positive and negative values."""
        scanner_signal = 0.8
        sentiment_signal = -0.3
        
        result = self.agent.combine_signals(scanner_signal, sentiment_signal)
        expected = (0.8 * 0.6) + (-0.3 * 0.4)  # 60/40 weights
        self.assertEqual(result, expected)
    
    def test_make_decision_long_positive_signal(self):
        """Test LONG decision with strong positive combined signal."""
        result = self.agent.make_decision(0.7, 0.5)
        
        self.assertEqual(result['decision'], TradeDecision.LONG.value)
        self.assertGreater(result['combined_signal'], 
                          STRATEGY_CONFIG['decision_thresholds']['long_min'])
    
    def test_make_decision_short_negative_signal(self):
        """Test SHORT decision with strong negative combined signal."""
        result = self.agent.make_decision(-0.7, -0.5)
        
        self.assertEqual(result['decision'], TradeDecision.SHORT.value)
        self.assertLess(result['combined_signal'], 
                       -STRATEGY_CONFIG['decision_thresholds']['short_min'])
    
    def test_make_decision_wait_weak_signal(self):
        """Test WAIT decision with weak combined signal."""
        result = self.agent.make_decision(0.1, -0.1)
        
        self.assertEqual(result['decision'], TradeDecision.WAIT.value)
        self.assertGreaterEqual(result['combined_signal'], 
                               -STRATEGY_CONFIG['decision_thresholds']['short_min'])
        self.assertLessEqual(result['combined_signal'], 
                            STRATEGY_CONFIG['decision_thresholds']['long_min'])
    
    def test_calculate_position_size_strong_signal(self):
        """Test position sizing with strong signal."""
        position_size = self.agent.calculate_position_size(0.8)
        
        # With strong signal, position should be larger than default
        self.assertGreater(position_size, 
                          STRATEGY_CONFIG['position_sizing']['default_allocation'])
        # But should not exceed max allocation
        self.assertLessEqual(position_size, 
                            STRATEGY_CONFIG['position_sizing']['max_allocation'])
    
    def test_calculate_position_size_weak_signal(self):
        """Test position sizing with weak signal."""
        position_size = self.agent.calculate_position_size(0.1)
        
        # With weak signal, position should be smaller
        self.assertLessEqual(position_size, 
                            STRATEGY_CONFIG['position_sizing']['default_allocation'])
    
    def test_calculate_position_size_zero_signal(self):
        """Test position sizing with zero signal."""
        position_size = self.agent.calculate_position_size(0.0)
        
        # With zero signal, position should be minimal
        self.assertEqual(position_size, 0.0)
    
    def test_make_decision_returns_correct_structure(self):
        """Test that decision returns correct structure."""
        result = self.agent.make_decision(0.6, 0.4)
        
        self.assertIn('decision', result)
        self.assertIn('combined_signal', result)
        self.assertIn('position_size', result)
        self.assertIn('signals', result)
        self.assertIn('scanner', result['signals'])
        self.assertIn('sentiment', result['signals'])
        self.assertIn('weights', result['signals'])
    
    def test_custom_config_update(self):
        """Test updating agent configuration."""
        new_config = {
            'signal_weights': {'scanner': 0.5, 'sentiment': 0.5},
            'decision_thresholds': {'long_min': 0.2, 'short_min': 0.2}
        }
        
        self.agent.update_config(new_config)
        
        # Verify config was updated
        self.assertEqual(self.agent.config['signal_weights']['scanner'], 0.5)
        self.assertEqual(self.agent.config['signal_weights']['sentiment'], 0.5)


if __name__ == '__main__':
    unittest.main()