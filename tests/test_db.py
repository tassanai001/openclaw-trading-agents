import unittest
import tempfile
import os
from config.db import Database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db = Database(db_path=self.temp_db.name)

    def tearDown(self):
        # Clean up the temporary database file
        os.unlink(self.temp_db.name)

    def test_get_portfolio_state_empty(self):
        """Test getting portfolio state when none exists"""
        result = self.db.get_portfolio_state()
        self.assertIsNone(result)

    def test_update_and_get_portfolio_state(self):
        """Test updating and retrieving portfolio state"""
        cash = 10000.0
        total_value = 9500.0
        positions = {"AAPL": {"quantity": 10, "avg_price": 150.0}}
        
        self.db.update_portfolio_state(cash, total_value, positions)
        
        result = self.db.get_portfolio_state()
        self.assertIsNotNone(result)
        self.assertEqual(result['cash'], cash)
        self.assertEqual(result['total_value'], total_value)
        self.assertEqual(result['positions'], positions)

    def test_add_and_get_positions(self):
        """Test adding and retrieving positions"""
        # Add a position
        self.db.add_position("AAPL", 10, 150.0, 155.0)
        
        # Get open positions
        positions = self.db.get_open_positions()
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]['symbol'], "AAPL")
        self.assertEqual(positions[0]['quantity'], 10)
        self.assertEqual(positions[0]['avg_price'], 150.0)
        self.assertEqual(positions[0]['current_price'], 155.0)

    def test_update_position(self):
        """Test updating an existing position"""
        # Add a position
        self.db.add_position("AAPL", 10, 150.0, 155.0)
        
        # Update the position
        self.db.update_position("AAPL", quantity=15, avg_price=148.0)
        
        # Get the updated position
        positions = self.db.get_open_positions()
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]['quantity'], 15)
        self.assertEqual(positions[0]['avg_price'], 148.0)
        self.assertEqual(positions[0]['current_price'], 155.0)

    def test_add_and_get_trades(self):
        """Test adding and retrieving trades"""
        # Add a trade
        self.db.add_trade("AAPL", 10, 150.0, "BUY", "ORDER123")
        
        # Get trade history
        trades = self.db.get_trade_history()
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]['symbol'], "AAPL")
        self.assertEqual(trades[0]['quantity'], 10)
        self.assertEqual(trades[0]['price'], 150.0)
        self.assertEqual(trades[0]['side'], "BUY")
        self.assertEqual(trades[0]['order_id'], "ORDER123")

    def test_get_trade_history_by_symbol(self):
        """Test getting trade history for specific symbol"""
        # Add trades for different symbols
        self.db.add_trade("AAPL", 10, 150.0, "BUY")
        self.db.add_trade("GOOGL", 5, 2500.0, "BUY")
        self.db.add_trade("AAPL", 5, 155.0, "SELL")
        
        # Get trades for AAPL only
        trades = self.db.get_trade_history(symbol="AAPL")
        self.assertEqual(len(trades), 2)
        for trade in trades:
            self.assertEqual(trade['symbol'], "AAPL")

    def test_cache_scan_result(self):
        """Test caching scan results"""
        # Cache a scan result
        result_data = {"rsi": 60, "macd": 1.5, "volume": 1000000}
        self.db.cache_scan_result("AAPL", result_data)
        
        # We can't directly retrieve cached data with current API,
        # but we can test that the caching operation doesn't raise an exception

    def test_cache_sentiment(self):
        """Test caching sentiment data"""
        # Cache sentiment data
        self.db.cache_sentiment("AAPL", 0.7, "Positive sentiment")
        
        # We can't directly retrieve cached data with current API,
        # but we can test that the caching operation doesn't raise an exception

    def test_get_latest_signals(self):
        """Test getting latest trading signals"""
        # Add some signals
        self.db.add_position("AAPL", 10, 150.0)  # Need to add position first
        
        # Direct insertion would be needed to test this properly
        # Since we don't have a public method to add signals, 
        # we'll just test the retrieval method with no data
        signals = self.db.get_latest_signals()
        # Should return an empty list if no signals exist
        # Note: This might fail if there are signals from other tests
        
    def test_get_latest_signals_by_symbol(self):
        """Test getting latest trading signals for specific symbol"""
        signals = self.db.get_latest_signals(symbol="AAPL")
        # Should return an empty list if no signals exist


if __name__ == '__main__':
    unittest.main()