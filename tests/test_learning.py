"""
Tests for the Learning Agent
"""
import unittest
import tempfile
import shutil
import os
from datetime import datetime, date
from agents.learning.learning import LearningAgent, PerformanceMetric
from agents.learning.config import LearningConfig


class TestLearningAgent(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test reports
        self.temp_dir = tempfile.mkdtemp()
        self.config = LearningConfig(reports_directory=self.temp_dir)
        self.agent = LearningAgent(self.config)
    
    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_record_performance_and_get_history(self):
        """Test recording performance metrics and maintaining history"""
        self.agent.record_performance(100.50, 10, 0.65, 0.05, -0.02)
        self.assertEqual(len(self.agent.performance_history), 1)
        
        # Add another record
        self.agent.record_performance(-50.25, 5, 0.60, 0.03, -0.01)
        self.assertEqual(len(self.agent.performance_history), 2)
        
        # Check the values
        first_record = self.agent.performance_history[0]
        self.assertEqual(first_record.profit_loss, 100.50)
        self.assertEqual(first_record.trades_count, 10)
        self.assertEqual(first_record.win_rate, 0.65)
        self.assertEqual(first_record.total_return, 0.05)
        self.assertEqual(first_record.max_drawdown, -0.02)
    
    def test_max_history_limit(self):
        """Test that history doesn't exceed the configured limit"""
        # Temporarily set a small limit
        small_config = LearningConfig(
            reports_directory=self.temp_dir,
            max_history_records=3
        )
        limited_agent = LearningAgent(small_config)
        
        # Add more records than the limit
        for i in range(5):
            limited_agent.record_performance(i*10, i+1, 0.5+i*0.1, i*0.01, -0.01)
        
        # Should only keep the last 3 records
        self.assertEqual(len(limited_agent.performance_history), 3)
    
    def test_generate_daily_report_empty(self):
        """Test generating a report when no data is available"""
        test_date = date(2023, 1, 1)
        report = self.agent.generate_daily_report(test_date)
        
        self.assertIn("# Daily Trading Report - 2023-01-01", report)
        self.assertIn("No trading activity recorded for this day", report)
    
    def test_generate_daily_report_with_data(self):
        """Test generating a report with actual performance data"""
        # Record some data for a specific date
        test_date = date(2023, 1, 1)
        
        # Mock the time to ensure consistent date
        metric1 = PerformanceMetric(
            timestamp=datetime.combine(test_date, datetime.min.time().replace(hour=10, minute=0)),
            profit_loss=100.50,
            trades_count=10,
            win_rate=0.65,
            total_return=0.05,
            max_drawdown=-0.02
        )
        metric2 = PerformanceMetric(
            timestamp=datetime.combine(test_date, datetime.min.time().replace(hour=14, minute=0)),
            profit_loss=-50.25,
            trades_count=5,
            win_rate=0.60,
            total_return=0.03,
            max_drawdown=-0.01
        )
        
        self.agent.performance_history = [metric1, metric2]
        
        report = self.agent.generate_daily_report(test_date)
        
        self.assertIn("# Daily Trading Report - 2023-01-01", report)
        self.assertIn("$50.25", report)  # Net profit (100.50 - 50.25)
        self.assertIn("15", report)      # Total trades (10 + 5)
        self.assertIn("0.62%", report) # Average win rate (65+60)/2
    
    def test_save_daily_report(self):
        """Test saving a daily report to file"""
        test_date = date(2023, 1, 1)
        
        # Record some data
        self.agent.record_performance(100.50, 10, 0.65, 0.05, -0.02)
        
        filepath = self.agent.save_daily_report(test_date)
        
        # Check that file was created
        self.assertTrue(os.path.exists(filepath))
        
        # Check that file has .md extension and correct date in name
        self.assertTrue(filepath.endswith(f"daily_report_{test_date.strftime('%Y%m%d')}.md"))
        
        # Check that file contains report content
        with open(filepath, 'r') as f:
            content = f.read()
            self.assertIn("# Daily Trading Report", content)
    
    def test_get_performance_summary(self):
        """Test getting overall performance summary"""
        # Record some data
        self.agent.record_performance(100.50, 10, 0.65, 0.05, -0.02)
        self.agent.record_performance(-50.25, 5, 0.60, 0.03, -0.01)
        self.agent.record_performance(75.00, 8, 0.70, 0.07, -0.03)
        
        summary = self.agent.get_performance_summary()
        
        self.assertEqual(summary['total_profit_loss'], 125.25)  # 100.50 - 50.25 + 75.00
        self.assertEqual(summary['total_trades'], 23)           # 10 + 5 + 8
        self.assertAlmostEqual(summary['average_win_rate'], 0.65, places=2)  # (0.65 + 0.60 + 0.70) / 3
        self.assertEqual(summary['maximum_return'], 0.07)
        self.assertEqual(summary['maximum_drawdown'], -0.03)
        self.assertEqual(summary['days_tracked'], 1)  # All records are from the same day by default
    
    def test_get_performance_summary_empty(self):
        """Test getting performance summary with no data"""
        summary = self.agent.get_performance_summary()
        self.assertEqual(summary, {})


if __name__ == '__main__':
    unittest.main()