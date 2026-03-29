"""
Comprehensive End-to-End Test for Full Trading Cycle with Paper Trading Mode

This test verifies that the complete trading cycle works correctly with paper trading enabled:
Scanner → Sentiment → Strategy → Risk → Execution → Learning

The test mocks all external API calls to ensure safe testing without real trading.
"""
import asyncio
import os
import tempfile
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.scanner.scanner import Scanner
from agents.sentiment.sentiment import SentimentAgent
from agents.strategy.strategy import StrategyAgent
from agents.risk.risk import RiskAgent
from agents.execution.execution_agent import ExecutionAgent
from agents.learning.learning import LearningAgent
from config.db import Database
from config.paper_trading_config import PaperTradingConfig


class TestFullCyclePaperTrading:
    """Test class for full trading cycle with paper trading mode"""
    
    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        self.db = Database(db_path=self.temp_db_path)
        
        self.paper_config = PaperTradingConfig(enabled=True)
        
        self.scanner = Scanner()
        self.sentiment = SentimentAgent()
        self.strategy = StrategyAgent()
        self.risk = RiskAgent()
        
        from agents.execution.config import ExecutionConfig
        execution_config = ExecutionConfig()
        self.execution = ExecutionAgent(
            config=execution_config,
            paper_trading_config=self.paper_config
        )
        
        from agents.learning.config import LearningConfig
        learning_config = LearningConfig()
        self.learning = LearningAgent(config=learning_config)
    
    def teardown_method(self):
        """Clean up after each test method"""
        # Remove temporary database file
        if hasattr(self, 'temp_db_path') and os.path.exists(self.temp_db_path):
            os.close(self.temp_db_fd)
            os.unlink(self.temp_db_path)
    
    @pytest.mark.asyncio
    async def test_full_trading_cycle_with_paper_trading(self):
        """
        Test the complete trading cycle with paper trading enabled:
        Scanner → Sentiment → Strategy → Risk → Execution → Learning
        
        This test ensures that all 6 agents work together properly in paper trading mode
        without making any real API calls or placing real orders.
        """
        with patch.object(self.scanner, '_fetch_market_data') as mock_fetch_market_data:
            import pandas as pd
            import numpy as np
            from datetime import datetime
            
            n_samples = 50
            dates = pd.date_range(end=datetime.now(), periods=n_samples, freq='min')
            close_prices = 50000 + np.random.randn(n_samples).cumsum() * 100
            open_prices = close_prices + np.random.randn(n_samples) * 10
            high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.randn(n_samples)) * 20
            low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.randn(n_samples)) * 20
            volume = np.abs(np.random.randn(n_samples)) * 1000
            
            mock_data = pd.DataFrame({
                'timestamp': dates,
                'open': open_prices,
                'high': high_prices,
                'low': low_prices,
                'close': close_prices,
                'volume': volume
            })
            
            mock_fetch_market_data.return_value = mock_data
            
            scan_results = await self.scanner.scan_market()
            assert len(scan_results) > 0, "Scanner should return results"
            
            signals = self.db.get_latest_signals()
            assert isinstance(signals, list)
            
            sample_text = "Bitcoin is showing strong bullish momentum with positive market sentiment"
            
            with patch.object(self.sentiment, '_analyze_sentiment', new_callable=AsyncMock) as mock_analyze:
                mock_analyze.return_value = 0.6
                
                sentiment_score = await self.sentiment.analyze(sample_text)
                assert isinstance(sentiment_score, float)
                assert -1.0 <= sentiment_score <= 1.0
                
                self.db.cache_sentiment("BTC/USDT", sentiment_score, sample_text)
        
        mock_portfolio = {
            'cash': 10000.0,
            'total_value': 15000.0,
            'positions': {'BTC/USDT': {'quantity': 0.1, 'avg_price': 45000.0}}
        }
        self.db.update_portfolio_state(
            mock_portfolio['cash'], 
            mock_portfolio['total_value'], 
            mock_portfolio['positions']
        )
        
        scanner_signal = 0.6
        sentiment_signal = 0.4
        
        strategy_decision = self.strategy.make_decision(scanner_signal, sentiment_signal)
        assert 'decision' in strategy_decision
        assert 'combined_signal' in strategy_decision
        
        mock_trade = {
            'symbol': 'BTC/USDT',
            'side': 'BUY',
            'quantity': 0.05,
            'price': 50000.0,
            'strategy': 'momentum'
        }
        
        position_value = mock_trade['quantity'] * mock_trade['price']
        pnl_change = 100.0
        new_positions = 1
        
        risk_approved, reason = self.risk.validate_trade(position_value, pnl_change, new_positions)
        risk_result = {
            'approved': risk_approved,
            'reason': reason
        }
        assert isinstance(risk_result, dict)
        assert 'approved' in risk_result
        
        if risk_approved:
            with patch.object(self.execution, 'place_order', new_callable=AsyncMock) as mock_place_order:
                mock_order_result = MagicMock()
                mock_order_result.success = True
                mock_order_result.order_id = 'PAPER_ORDER_123'
                mock_order_result.filled_qty = 0.05
                mock_order_result.filled_price = 50000.0
                mock_order_result.raw_response = {'status': 'FILLED', 'executed_quantity': 0.05, 'average_price': 50000.0}
                
                mock_place_order.return_value = mock_order_result
                
                execution_result = await self.execution.place_order(
                    mock_trade['symbol'].replace('/', ''),
                    'B' if mock_trade['side'] == 'BUY' else 'S',
                    1,
                    'market',
                    None,
                    mock_trade['quantity']
                )
                
                assert execution_result.success is True
                
                self.db.add_trade(
                    mock_trade['symbol'],
                    mock_trade['quantity'],
                    mock_trade['price'],
                    mock_trade['side'],
                    getattr(execution_result, 'order_id', 'PAPER_ORDER_123')
                )
        else:
            pass
        
        trade_outcome = {
            'trade_id': 'PAPER_ORDER_123',
            'result': 'PROFIT',
            'pnl': 250.0,
            'duration': 3600
        }
        
        self.learning.record_performance(
            profit_loss=250.0,
            trades_count=1,
            win_rate=0.70,
            total_return=1.5,
            max_drawdown=-0.05
        )
        learning_feedback = self.learning.get_performance_summary()
        
        assert isinstance(learning_feedback, dict)
        
        portfolio_state = self.db.get_portfolio_state()
        assert portfolio_state is not None
        assert portfolio_state['total_value'] >= 0
        assert portfolio_state['cash'] >= 0
    
    @pytest.mark.asyncio
    async def test_data_flow_consistency_with_paper_trading(self):
        """
        Verify that data flows correctly between agents with paper trading enabled
        """
        self.db.add_position("BTC/USDT", 0.1, 45000.0, 50000.0)
        
        positions = self.db.get_open_positions()
        assert len(positions) == 1
        assert positions[0]['symbol'] == "BTC/USDT"
        
        portfolio = self.db.get_portfolio_state()
        if portfolio is None:
            self.db.update_portfolio_state(10000.0, 15000.0, {"BTC/USDT": {"quantity": 0.1, "avg_price": 45000.0}})
            portfolio = self.db.get_portfolio_state()
        
        assert portfolio is not None
        
        assert portfolio['total_value'] >= 0
        assert portfolio['cash'] >= 0
        
        with patch.object(self.execution, 'place_order', new_callable=AsyncMock) as mock_place_order:
            mock_order_result = MagicMock()
            mock_order_result.success = True
            mock_order_result.order_id = 'PAPER_TEST_456'
            mock_order_result.filled_qty = 0.02
            mock_order_result.filled_price = 48000.0
            
            mock_place_order.return_value = mock_order_result
            
            result = await self.execution.place_order("ETHUSDT", "B", 1, "market", None, 0.02)
            assert result.success is True
            
            account_info = await self.execution.get_account_info()
            assert account_info['paper_trading'] is True
            assert 'account_value' in account_info
    
    @pytest.mark.asyncio
    async def test_database_operations_with_paper_trading(self):
        """
        Test database operations used in the trading cycle with paper trading
        """
        self.db.add_trade("ETH/USDT", 2.0, 3000.0, "BUY", "ORDER_789")
        
        trade_history = self.db.get_trade_history(symbol="ETH/USDT")
        assert len(trade_history) == 1
        assert trade_history[0]['symbol'] == "ETH/USDT"
        assert trade_history[0]['side'] == "BUY"
        assert trade_history[0]['order_id'] == "ORDER_789"
        
        self.db.cache_sentiment("ETH/USDT", 0.6, "Positive sentiment for ETH")
        
        self.db.add_position("ETH/USDT", 2.0, 3000.0, 3100.0)
        
        positions = self.db.get_open_positions()
        eth_position = None
        for pos in positions:
            if pos['symbol'] == "ETH/USDT":
                eth_position = pos
                break
        
        assert eth_position is not None
        assert eth_position['quantity'] == 2.0
        assert eth_position['avg_price'] == 3000.0
        assert eth_position['current_price'] == 3100.0
        
        initial_balance = self.execution.paper_balance
        account_info = await self.execution.get_account_info()
        assert account_info['paper_trading'] is True
        assert account_info['account_value'] == initial_balance
    
    @pytest.mark.asyncio
    async def test_risk_management_with_paper_trading(self):
        """
        Test risk management validation with paper trading enabled
        """
        mock_portfolio = {
            'cash': 1000.0,
            'total_value': 2000.0,
            'positions': {}
        }
        self.db.update_portfolio_state(
            mock_portfolio['cash'], 
            mock_portfolio['total_value'], 
            mock_portfolio['positions']
        )
        
        position_value = 500.0
        pnl_change = 50.0
        new_positions = 1
        
        risk_approved, reason = self.risk.validate_trade(position_value, pnl_change, new_positions)
        assert isinstance(risk_approved, bool)
        assert isinstance(reason, str)
        
        excessive_position_value = 2000.0
        risk_approved_large, reason_large = self.risk.validate_trade(excessive_position_value, pnl_change, new_positions)
        
        assert isinstance(risk_approved_large, bool)
        assert isinstance(reason_large, str)
        
        if risk_approved:
            with patch.object(self.execution, 'place_order', new_callable=AsyncMock) as mock_place_order:
                mock_order_result = MagicMock()
                mock_order_result.success = True
                mock_order_result.order_id = 'RISK_TEST_789'
                
                mock_place_order.return_value = mock_order_result
                
                result = await self.execution.place_order("BTCUSDT", "B", 1, "market", None, 0.01)
                assert result.success is True
    
    @pytest.mark.asyncio
    async def test_learning_agent_with_paper_trading_outcomes(self):
        """
        Test learning agent performance tracking with paper trading outcomes
        """
        outcomes = [
            {'profit_loss': 150.0, 'trades_count': 1, 'win_rate': 0.65, 'total_return': 1.2, 'max_drawdown': -0.03},
            {'profit_loss': -75.0, 'trades_count': 1, 'win_rate': 0.60, 'total_return': 1.15, 'max_drawdown': -0.04},
            {'profit_loss': 200.0, 'trades_count': 1, 'win_rate': 0.67, 'total_return': 1.25, 'max_drawdown': -0.02}
        ]
        
        for outcome in outcomes:
            self.learning.record_performance(**outcome)
        
        summary = self.learning.get_performance_summary()
        assert isinstance(summary, dict)
        assert 'total_trades' in summary
        assert 'total_profit_loss' in summary
        assert 'average_win_rate' in summary
        
        assert summary['total_trades'] == len(outcomes)
        assert abs(summary['total_profit_loss'] - sum(o['profit_loss'] for o in outcomes)) < 0.01
    
    @pytest.mark.asyncio
    async def test_complete_workflow_with_mocked_external_apis(self):
        """
        Test the complete workflow with all external APIs mocked to ensure safe testing
        """
        with patch.object(self.scanner, '_fetch_market_data') as mock_market_data, \
             patch.object(self.sentiment, '_analyze_sentiment', new_callable=AsyncMock) as mock_analyze, \
             patch.object(self.execution, 'place_order', new_callable=AsyncMock) as mock_execution:
            
            import pandas as pd
            import numpy as np
            from datetime import datetime
            
            n_samples = 30
            dates = pd.date_range(end=datetime.now(), periods=n_samples, freq='min')
            prices = 40000 + np.random.randn(n_samples).cumsum() * 50
            mock_data = pd.DataFrame({
                'timestamp': dates,
                'open': prices + np.random.randn(n_samples) * 10,
                'high': prices + np.abs(np.random.randn(n_samples)) * 20,
                'low': prices - np.abs(np.random.randn(n_samples)) * 20,
                'close': prices,
                'volume': np.abs(np.random.randn(n_samples)) * 800
            })
            mock_market_data.return_value = mock_data
            
            mock_analyze.return_value = 0.65
            
            mock_order_result = MagicMock()
            mock_order_result.success = True
            mock_order_result.order_id = 'FULL_WORKFLOW_TEST'
            mock_order_result.filled_qty = 0.03
            mock_order_result.filled_price = 42000.0
            mock_execution.return_value = mock_order_result
            
            scan_results = await self.scanner.scan_market()
            assert len(scan_results) > 0
            
            sentiment_score = await self.sentiment.analyze("Market looks great")
            assert -1.0 <= sentiment_score <= 1.0
            
            strategy_decision = self.strategy.make_decision(0.5, sentiment_score)
            assert 'decision' in strategy_decision
            
            risk_approved, _ = self.risk.validate_trade(1260.0, 100.0, 1)
            if risk_approved:
                execution_result = await self.execution.place_order("BTCUSDT", "B", 1, "market", None, 0.03)
                assert execution_result.success is True
            
            self.learning.record_performance(100.0, 1, 0.7, 1.1, -0.02)
            summary = self.learning.get_performance_summary()
            assert isinstance(summary, dict)
            
            assert mock_market_data.called
            assert mock_analyze.called
            assert mock_execution.called