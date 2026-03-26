"""
Tests for Risk Agent
"""
import unittest
from agents.risk.risk import RiskAgent


class TestRiskAgent(unittest.TestCase):
    """Test cases for RiskAgent class"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.risk_agent = RiskAgent(initial_account_value=100000.0)
    
    def test_initialization(self):
        """Test RiskAgent initialization"""
        self.assertEqual(self.risk_agent.initial_account_value, 100000.0)
        self.assertEqual(self.risk_agent.current_account_value, 100000.0)
        self.assertEqual(self.risk_agent.daily_pnl, 0.0)
        self.assertEqual(self.risk_agent.positions_count, 0)
    
    def test_check_position_size_within_limit(self):
        """Test position size check for valid positions (under 2%)"""
        # 1% position should be valid (2000 < 2000 limit at 100k account)
        is_valid, reason = self.risk_agent.check_position_size(1000.0)
        self.assertTrue(is_valid, f"Expected valid position, got: {reason}")
        
        # Exactly 2% should be valid
        is_valid, reason = self.risk_agent.check_position_size(2000.0)
        self.assertTrue(is_valid, f"Expected valid position, got: {reason}")
    
    def test_check_position_size_exceeds_limit(self):
        """Test position size check for invalid positions (over 2%)"""
        # 3% position should be rejected (3000 > 2000 limit at 100k account)
        is_valid, reason = self.risk_agent.check_position_size(3000.0)
        self.assertFalse(is_valid)
        self.assertIn("exceeds 2% limit", reason)
    
    def test_check_daily_loss_limit_valid(self):
        """Test daily loss limit check for valid trades"""
        # Small loss should be valid
        is_valid, reason = self.risk_agent.check_daily_loss_limit(-100.0)
        self.assertTrue(is_valid, f"Expected valid trade, got: {reason}")
        
        # At limit should be valid
        is_valid, reason = self.risk_agent.check_daily_loss_limit(-5000.0)
        self.assertTrue(is_valid, f"Expected valid trade, got: {reason}")
    
    def test_check_daily_loss_limit_exceeded(self):
        """Test daily loss limit check for invalid trades"""
        # Trade exceeding 5% loss limit should be rejected
        is_valid, reason = self.risk_agent.check_daily_loss_limit(-6000.0)
        self.assertFalse(is_valid)
        self.assertIn("would exceed daily loss limit", reason)
    
    def test_check_max_positions_valid(self):
        """Test max positions check for valid additions"""
        # Adding up to 5 positions should be valid
        self.risk_agent.update_positions_count(4)  # Already have 4
        is_valid, reason = self.risk_agent.check_max_positions(1)  # Add 1 more
        self.assertTrue(is_valid, f"Expected valid addition, got: {reason}")
    
    def test_check_max_positions_exceeded(self):
        """Test max positions check for invalid additions"""
        # Adding beyond 5 positions should be rejected
        self.risk_agent.update_positions_count(5)  # Already have 5
        is_valid, reason = self.risk_agent.check_max_positions(1)  # Try to add 1 more
        self.assertFalse(is_valid)
        self.assertIn("would exceed maximum of 5 positions", reason)
    
    def test_validate_trade_all_checks_pass(self):
        """Test that validate_trade passes when all checks pass"""
        is_valid, reason = self.risk_agent.validate_trade(
            position_value=1500.0,  # Within 2% limit
            pnl_change=-100.0,      # Within daily loss limit
            new_positions=1         # Within max positions
        )
        self.assertTrue(is_valid, f"Expected valid trade, got: {reason}")
    
    def test_validate_trade_fails_position_size(self):
        """Test that validate_trade fails when position size check fails"""
        is_valid, reason = self.risk_agent.validate_trade(
            position_value=15000.0,  # Exceeds 2% limit
            pnl_change=-100.0,       # Within daily loss limit
            new_positions=1          # Within max positions
        )
        self.assertFalse(is_valid)
        self.assertIn("exceeds 2%", reason)
    
    def test_validate_trade_fails_daily_loss(self):
        """Test that validate_trade fails when daily loss check fails"""
        is_valid, reason = self.risk_agent.validate_trade(
            position_value=1500.0,   # Within 2% limit
            pnl_change=-6000.0,      # Exceeds daily loss limit
            new_positions=1          # Within max positions
        )
        self.assertFalse(is_valid)
        self.assertIn("would exceed daily loss limit", reason)
    
    def test_validate_trade_fails_max_positions(self):
        """Test that validate_trade fails when max positions check fails"""
        self.risk_agent.update_positions_count(5)  # Already at max
        is_valid, reason = self.risk_agent.validate_trade(
            position_value=1500.0,   # Within 2% limit
            pnl_change=-100.0,       # Within daily loss limit
            new_positions=1          # Would exceed max positions
        )
        self.assertFalse(is_valid)
        self.assertIn("would exceed maximum of 5 positions", reason)
    
    def test_update_account_value(self):
        """Test updating account value"""
        self.risk_agent.update_account_value(120000.0)
        self.assertEqual(self.risk_agent.current_account_value, 120000.0)
    
    def test_update_daily_pnl(self):
        """Test updating daily P&L"""
        self.risk_agent.update_daily_pnl(-500.0)
        self.assertEqual(self.risk_agent.daily_pnl, -500.0)
        
        # Add more P&L
        self.risk_agent.update_daily_pnl(200.0)
        self.assertEqual(self.risk_agent.daily_pnl, -300.0)
    
    def test_update_positions_count(self):
        """Test updating positions count"""
        self.risk_agent.update_positions_count(3)
        self.assertEqual(self.risk_agent.positions_count, 3)
        
        # Close 1 position
        self.risk_agent.update_positions_count(-1)
        self.assertEqual(self.risk_agent.positions_count, 2)
    
    def test_get_risk_status(self):
        """Test getting risk status"""
        status = self.risk_agent.get_risk_status()
        
        expected_keys = [
            'account_value', 'daily_pnl', 'positions_count',
            'max_daily_loss', 'max_position_size', 'max_positions',
            'remaining_daily_loss', 'remaining_positions'
        ]
        
        for key in expected_keys:
            self.assertIn(key, status)
        
        self.assertEqual(status['account_value'], 100000.0)
        self.assertEqual(status['daily_pnl'], 0.0)
        self.assertEqual(status['positions_count'], 0)
        self.assertEqual(status['max_positions'], 5)


if __name__ == '__main__':
    unittest.main()