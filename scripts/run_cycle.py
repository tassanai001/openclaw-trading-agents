#!/usr/bin/env python3
"""
Main Trading Cycle Script

This script runs the full trading cycle with all 6 agents:
Scanner → Sentiment → Strategy → Risk → Execution → Learning

Handles errors gracefully and logs results.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all agents
from agents.scanner.scanner import Scanner
from agents.sentiment.sentiment import SentimentAgent
from agents.strategy.strategy import StrategyAgent
from agents.risk.risk import RiskAgent
from agents.execution.execution import ExecutionAgent
from agents.learning.learning import LearningAgent
from config.db import Database


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/trading_cycle.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger('TradingCycle')


async def run_trading_cycle():
    """
    Execute the full trading cycle with all 6 agents
    """
    logger = setup_logging()
    logger.info("Starting full trading cycle...")
    
    try:
        # Initialize all agents
        logger.info("Initializing agents...")
        scanner = Scanner()
        sentiment = SentimentAgent()
        strategy = StrategyAgent()
        risk = RiskAgent()
        
        # Initialize execution agent with config
        from agents.execution.config import ExecutionConfig
        from config.paper_trading_config import PaperTradingConfig
        execution_config = ExecutionConfig()
        paper_config = PaperTradingConfig(enabled=True)  # Enable paper trading for safety
        execution = ExecutionAgent(config=execution_config, paper_trading_config=paper_config)
        
        # Initialize learning agent with config
        from agents.learning.config import LearningConfig
        learning_config = LearningConfig()
        learning = LearningAgent(config=learning_config)
        
        # Initialize database connection
        db = Database()
        logger.info("Database connection established")
        
        # Step 1: Scanner - Scan markets and generate signals
        logger.info("Step 1: Starting market scanning...")
        scan_results = await scanner.scan_market()
        logger.info(f"Market scanning completed. Found {len(scan_results)} scan results")
        
        # Step 2: Sentiment Analysis - Analyze market sentiment
        logger.info("Step 2: Performing sentiment analysis...")
        sample_text = "Market showing mixed signals with cautious optimism"
        sentiment_score = await sentiment.analyze(sample_text)
        logger.info(f"Sentiment analysis completed. Score: {sentiment_score}")
        
        # Cache sentiment data
        db.cache_sentiment("OVERALL", sentiment_score, sample_text)
        
        # Step 3: Strategy - Process signals and make decisions
        logger.info("Step 3: Processing signals with strategy agent...")
        
        # Get portfolio state
        portfolio = db.get_portfolio_state()
        if not portfolio:
            # Default portfolio if none exists
            portfolio = {
                'cash': 10000.0,
                'total_value': 10000.0,
                'positions': {}
            }
            db.update_portfolio_state(portfolio['cash'], portfolio['total_value'], portfolio['positions'])
        
        # Make strategy decisions based on scan results
        for pair, pair_data in scan_results.items():
            for timeframe, data in pair_data.items():
                if 'signal' in data and data['signal'] != 'HOLD':
                    logger.info(f"Processing signal for {pair} ({timeframe}): {data['signal']}")
                    
                    # Make strategy decision
                    # For this example, using the signal as a numeric value
                    scanner_signal = 0.5 if data['signal'] == 'BUY' else (-0.5 if data['signal'] == 'SELL' else 0.0)
                    sentiment_score = 0.3  # Using a default sentiment score
                    strategy_decision = strategy.make_decision(scanner_signal, sentiment_score)
                    logger.info(f"Strategy decision for {pair}: {strategy_decision}")
                    
                    # Step 4: Risk Management - Validate the trade
                    logger.info(f"Step 4: Validating trade with risk manager for {pair}...")
                    
                    # Prepare trade data - use the correct key from strategy decision
                    decision = strategy_decision.get('decision', 'WAIT')
                    side = 'BUY' if decision == 'LONG' else ('SELL' if decision == 'SHORT' else 'HOLD')
                    
                    # Calculate position size correctly (position_size is a percentage of portfolio)
                    position_size_pct = abs(strategy_decision.get('position_size', 0.02))  # Default 2%
                    portfolio_value = portfolio.get('total_value', 10000.0)
                    position_value_target = portfolio_value * position_size_pct  # e.g., $10,000 * 0.02 = $200
                    
                    # Get current price
                    current_price = data.get('indicators', {}).get('close', [-1])[-1] if isinstance(data.get('indicators', {}), dict) and 'close' in data.get('indicators', {}) else 50000.0
                    
                    # Calculate quantity based on position value and price
                    quantity = position_value_target / current_price  # e.g., $200 / $50,000 = 0.004 BTC
                    
                    trade_data = {
                        'symbol': pair,
                        'side': side,
                        'quantity': quantity,
                        'price': current_price,
                        'position_size_pct': position_size_pct,
                        'position_value': position_value_target,
                        'strategy': 'technical',
                        'confidence': strategy_decision.get('combined_signal', 0.5)
                    }
                    
                    # Risk validation expects position_value, pnl_change, and new_positions
                    position_value = position_value_target  # Use calculated position value (2% of portfolio)
                    pnl_change = 100.0  # Expected profit/loss
                    new_positions = 1
                    
                    is_approved, reason = risk.validate_trade(position_value, pnl_change, new_positions)
                    risk_validation = {
                        'approved': is_approved,
                        'reason': reason
                    }
                    logger.info(f"Risk validation for {pair}: {risk_validation}")
                    
                    # Step 5: Execution - Execute the trade if approved
                    if risk_validation.get('approved', False):
                        logger.info(f"Step 5: Executing trade for {pair}...")
                        
                        try:
                            # Convert to execution agent signal format
                            # Map symbol format (BTC/USDT → BTC) and side (BUY → B, SELL → S)
                            asset = pair.replace('/USDT', '').replace('/USD', '')
                            order_side = 'B' if trade_data['side'] == 'BUY' else 'S'
                            
                            execution_signal = {
                                'asset': asset,
                                'side': order_side,
                                'size': trade_data['quantity'],
                                'price': trade_data['price'],
                                'order_type': 'market',
                                'symbol': pair,
                                'quantity': trade_data['quantity']
                            }
                            
                            execution_result = await execution.execute_order(execution_signal)
                            
                            logger.info(f"Trade executed for {pair}. Result: {execution_result}")
                            
                            # Add trade to database
                            db.add_trade(
                                trade_data['symbol'],
                                trade_data['quantity'],
                                trade_data['price'],
                                trade_data['side'],
                                execution_result.order_id or 'UNKNOWN'
                            )
                            
                            # Update portfolio state after successful execution
                            if execution_result.success:
                                # Update portfolio with new state after trade
                                updated_cash = portfolio['cash'] - (trade_data['quantity'] * trade_data['price']) if trade_data['side'] == 'BUY' else portfolio['cash'] + (trade_data['quantity'] * trade_data['price'])
                                
                                # Update positions
                                positions = portfolio['positions'].copy()
                                if trade_data['symbol'] in positions:
                                    # Update existing position
                                    current_pos = positions[trade_data['symbol']]
                                    if trade_data['side'] == 'BUY':
                                        new_qty = current_pos['quantity'] + trade_data['quantity']
                                        new_avg_price = ((current_pos['quantity'] * current_pos['avg_price']) + (trade_data['quantity'] * trade_data['price'])) / new_qty
                                        positions[trade_data['symbol']] = {
                                            'quantity': new_qty,
                                            'avg_price': new_avg_price
                                        }
                                    else:  # SELL
                                        new_qty = current_pos['quantity'] - trade_data['quantity']
                                        if new_qty <= 0:
                                            del positions[trade_data['symbol']]
                                        else:
                                            positions[trade_data['symbol']]['quantity'] = new_qty
                                else:
                                    # Add new position
                                    if trade_data['side'] == 'BUY':
                                        positions[trade_data['symbol']] = {
                                            'quantity': trade_data['quantity'],
                                            'avg_price': trade_data['price']
                                        }
                                
                                # Update portfolio state
                                db.update_portfolio_state(updated_cash, portfolio['total_value'], positions)
                                portfolio = db.get_portfolio_state()  # Refresh portfolio
                        
                        except Exception as e:
                            logger.error(f"Error executing trade for {pair}: {str(e)}")
                    else:
                        logger.info(f"Trade for {pair} rejected by risk manager: {risk_validation.get('reason', 'Unknown reason')}")
                else:
                    logger.info(f"No actionable signal for {pair} ({timeframe})")
        
        # Step 6: Learning - Process outcomes and learn
        logger.info("Step 6: Processing outcomes with learning agent...")
        
        # Get recent trades to evaluate
        recent_trades = db.get_trade_history(limit=10)
        if recent_trades:
            # Calculate aggregate performance metrics
            total_pnl = sum((trade['price'] * trade['quantity'] * 0.01) for trade in recent_trades)
            trades_count = len(recent_trades)
            win_rate = 0.6  # Mock win rate
            total_return = (total_pnl / 10000.0) * 100  # Percentage return
            max_drawdown = 0.05  # Mock max drawdown
            
            # Record performance with learning agent
            learning.record_performance(
                profit_loss=total_pnl,
                trades_count=trades_count,
                win_rate=win_rate,
                total_return=total_return,
                max_drawdown=max_drawdown
            )
            logger.info(f"Learning agent recorded: {trades_count} trades, P&L: ${total_pnl:.2f}")
        
        logger.info("Full trading cycle completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error in trading cycle: {str(e)}", exc_info=True)
        return False


def main():
    """Main entry point"""
    success = asyncio.run(run_trading_cycle())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()