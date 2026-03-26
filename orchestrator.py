"""
Main Orchestrator
Coordinates all trading agents in the correct order, handles errors and retries,
and logs results to database and markdown files.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

from config.orchestrator_config import (
    AGENT_ORDER, AGENT_TIMEOUTS, MAX_RETRIES, RETRY_DELAY, 
    TRADING_CYCLE_INTERVAL, ENABLE_LOGGING, LOG_TO_DATABASE, LOG_TO_MARKDOWN
)

# Import real agent classes with wrapper adapters for uniform interface

# Scanner Agent
try:
    from agents.scanner.scanner import Scanner as _Scanner
    class ScannerAgent:
        def __init__(self):
            self._agent = _Scanner()
        async def run(self, data=None):
            # Scanner returns signals dict, extract signal strength
            if hasattr(self._agent, 'scan_market'):
                result = await self._agent.scan_market()
                # Get average signal strength from all pairs and timeframes
                signals = []
                if result:
                    for pair, timeframes in result.items():
                        for tf, data in timeframes.items():
                            if isinstance(data, dict) and 'signal' in data:
                                sig = data['signal']
                                if isinstance(sig, (int, float)):
                                    signals.append(float(sig))
                signal_strength = sum(signals) / len(signals) if signals else 0.0
                return {"status": "success", "scanner_signal": signal_strength, "signals": result}
            return {"status": "success", "scanner_signal": 0.0}
except ImportError:
    class ScannerAgent:
        async def run(self, data=None): return {"status": "success", "scanner_signal": 0.0}

# Sentiment Agent
try:
    from agents.sentiment.sentiment import SentimentAgent as _SentimentAgent
    class SentimentAgent:
        def __init__(self):
            self._agent = _SentimentAgent()
        async def run(self, data=None):
            # Get sentiment score from combined result
            if hasattr(self._agent, 'get_overall_sentiment'):
                result = await self._agent.get_overall_sentiment(include_fng=True)
                sentiment_score = 0.0
                if isinstance(result, dict) and 'combined' in result:
                    sentiment_score = result['combined'].get('sentiment_score', 0.0)
                return {"status": "success", "sentiment": sentiment_score, "sentiment_score": sentiment_score, "full_result": result}
            return {"status": "success", "sentiment": 0.0, "sentiment_score": 0.0}
except ImportError:
    class SentimentAgent:
        async def run(self, data=None): return {"status": "success", "sentiment": 0.0, "sentiment_score": 0.0}

# Strategy Agent
try:
    from agents.strategy.strategy import StrategyAgent as _StrategyAgent
    class StrategyAgent:
        def __init__(self):
            self._agent = _StrategyAgent()
        async def run(self, data=None):
            # Extract signals from scanner and sentiment results
            scanner_signal = 0.5
            sentiment_signal = 0.5
            
            if data:
                # From scanner results (take first/primary asset)
                if 'scanner' in data and isinstance(data['scanner'], dict):
                    results = data['scanner'].get('results', [])
                    if results and isinstance(results, list) and len(results) > 0:
                        scanner_signal = results[0].get('signal', 0.5)
                
                # From sentiment results
                if 'sentiment' in data and isinstance(data['sentiment'], dict):
                    results = data['sentiment'].get('results', [])
                    if results and isinstance(results, list) and len(results) > 0:
                        sentiment_signal = results[0].get('sentiment_score', 0.5)
            
            decision = self._agent.make_decision(scanner_signal, sentiment_signal)
            
            # Add pair info for execution
            if 'scanner' in data and isinstance(data['scanner'], dict):
                results = data['scanner'].get('results', [])
                if results and isinstance(results, list) and len(results) > 0:
                    asset = results[0].get('asset', 'BTC')
                    decision['pair'] = f"{asset}/USDT"
            else:
                decision['pair'] = "BTC/USDT"
            
            # Reduce position size to avoid exceeding limits (max 10% of account)
            if 'position_size' in decision:
                decision['position_size'] = min(decision['position_size'], 0.001)  # Max 0.001 BTC
            
            return {"status": "success", "strategy": decision, "decision": decision}
except ImportError:
    class StrategyAgent:
        async def run(self, data=None): return {"status": "success", "strategy": data or {}}

# Risk Agent
try:
    from agents.risk.risk import RiskAgent as _RiskAgent
    class RiskAgent:
        def __init__(self):
            self._agent = _RiskAgent()
        async def run(self, data=None):
            if hasattr(self._agent, 'assess'):
                result = await self._agent.assess(data or {})
                return {"status": "success", "risk": result}
            return {"status": "success", "risk": data or {}}
except ImportError:
    class RiskAgent:
        async def run(self, data=None): return {"status": "success", "risk": data or {}}

# Execution Agent (Adapter Pattern - Binance Demo/Hyperliquid)
try:
    from agents.execution.execution_agent import ExecutionAgent as _ExecutionAgent
    import os
    
    class ExecutionAgent:
        def __init__(self):
            # Get exchange from environment (default: binance)
            exchange = os.getenv('ACTIVE_EXCHANGE', 'binance')
            self._agent = _ExecutionAgent(exchange=exchange)
            self._initialized = False
            
        async def _ensure_initialized(self):
            if not self._initialized:
                await self._agent.initialize()
                self._initialized = True
            
        async def run(self, data=None):
            # Ensure adapter is initialized
            await self._ensure_initialized()
            
            # data structure: {'status': 'success', 'risk': {'status': 'success', 'strategy': {'decision': {...}}}}
            if data and isinstance(data, dict):
                # Navigate to decision
                decision = None
                if 'decision' in data:
                    decision = data['decision']
                elif 'risk' in data and isinstance(data['risk'], dict):
                    if 'decision' in data['risk']:
                        decision = data['risk']['decision']
                    elif 'strategy' in data['risk'] and isinstance(data['risk']['strategy'], dict):
                        decision = data['risk']['strategy'].get('decision', {})
                
                if decision and isinstance(decision, dict) and decision.get('decision') in ['LONG', 'SHORT', 'WAIT']:
                    asset = decision.get('pair', 'BTC/USDT').split('/')[0]
                    decision_type = decision.get('decision')
                    combined_signal = decision.get('combined_signal', 0.0)
                    position_size = decision.get('position_size', 0.001)
                    
                    # Execute trade using new adapter-based execution
                    try:
                        # Get current price
                        symbol = f"{asset}USDT"
                        price = await self._agent.adapter.get_ticker_price(symbol)
                        
                        # Place order
                        from agents.execution.models.order import Order
                        from agents.execution.models.common import OrderSide, OrderType
                        
                        side = OrderSide.BUY if decision_type == 'LONG' else OrderSide.SELL
                        
                        # Skip if WAIT/HOLD signal
                        if decision_type == 'WAIT' or abs(combined_signal) < 0.2:
                            return {
                                "status": "success",
                                "execution": {
                                    "success": True,
                                    "action": "HOLD",
                                    "reason": f"Signal {combined_signal:.3f} within HOLD range"
                                },
                                "paper_trading": False
                            }
                        
                        order = Order(
                            symbol=symbol,
                            side=side,
                            type=OrderType.MARKET,
                            quantity=position_size
                        )
                        
                        result = await self._agent.adapter.place_order(order)
                        
                        return {
                            "status": "success",
                            "execution": {
                                "success": result.success,
                                "action": decision_type,
                                "order_id": result.order_id,
                                "filled_quantity": result.filled_quantity,
                                "filled_price": result.filled_price,
                                "fee": result.fee,
                                "error": result.message if not result.success else None
                            },
                            "paper_trading": False
                        }
                        
                    except Exception as e:
                        return {
                            "status": "error",
                            "execution": {
                                "success": False,
                                "error": str(e)
                            },
                            "paper_trading": False
                        }
                        
            return {"status": "success", "execution": {}, "paper_trading": False}
            
except ImportError as e:
    print(f"Warning: Could not import new ExecutionAgent: {e}")
    class ExecutionAgent:
        async def run(self, data=None): return {"status": "success", "execution": data or {}}

# Learning Agent
try:
    from agents.learning.learning import LearningAgent as _LearningAgent
    from agents.learning.config import LearningConfig
    class LearningAgent:
        def __init__(self):
            config = LearningConfig() if hasattr(__import__('agents.learning.config', fromlist=['LearningConfig']), 'LearningConfig') else None
            self._agent = _LearningAgent(config) if config else _LearningAgent()
        async def run(self, data=None):
            if hasattr(self._agent, 'learn'):
                result = await self._agent.learn(data or {})
                return {"status": "success", "learning": result}
            return {"status": "success", "learning": data or {}}
except ImportError:
    class LearningAgent:
        async def run(self, data=None): return {"status": "success", "learning": data or {}}


class TradingOrchestrator:
    """Main orchestrator that manages the trading cycle."""
    
    def __init__(self):
        self.agents = {}
        self.logger = self._setup_logger()
        self._initialize_agents()
        
    def _setup_logger(self):
        """Set up logger for the orchestrator."""
        logger = logging.getLogger('TradingOrchestrator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _initialize_agents(self):
        """Initialize all trading agents."""
        agent_classes = {
            "scanner": ScannerAgent,
            "sentiment": SentimentAgent,
            "strategy": StrategyAgent,
            "risk": RiskAgent,
            "execution": ExecutionAgent,
            "learning": LearningAgent
        }
        
        for agent_name in AGENT_ORDER:
            try:
                self.agents[agent_name] = agent_classes[agent_name]()
                self.logger.info(f"Initialized agent: {agent_name}")
            except KeyError:
                self.logger.error(f"Agent class not found: {agent_name}")
            except Exception as e:
                self.logger.error(f"Error initializing agent {agent_name}: {e}")
    
    async def run_single_cycle(self) -> Dict:
        """
        Run a single trading cycle with all agents in the correct order.
        Returns the results of the cycle.
        """
        cycle_results = {}
        accumulated_data = {}  # Accumulate all agent results
        
        for agent_name in AGENT_ORDER:
            agent = self.agents.get(agent_name)
            if not agent:
                self.logger.error(f"Agent {agent_name} not initialized")
                continue
                
            # Try to run agent with retries
            success = False
            attempt = 0
            
            while not success and attempt < MAX_RETRIES:
                try:
                    self.logger.info(f"Running agent: {agent_name} (attempt {attempt + 1})")
                    
                    # Pass accumulated data to all agents
                    agent_input = accumulated_data.copy()
                    
                    # Run the agent with timeout
                    timeout = AGENT_TIMEOUTS.get(agent_name, 30)
                    result = await asyncio.wait_for(
                        agent.run(agent_input), 
                        timeout=timeout
                    )
                    
                    cycle_results[agent_name] = result
                    
                    # Accumulate results for next agents
                    if agent_name == 'scanner':
                        accumulated_data['scanner_signal'] = result.get('scanner_signal', 0.0)
                    elif agent_name == 'sentiment':
                        accumulated_data['sentiment'] = result.get('sentiment_score', 0.0)
                        accumulated_data['sentiment_score'] = result.get('sentiment_score', 0.0)
                    elif agent_name == 'strategy':
                        accumulated_data['strategy'] = result.get('strategy', {})
                        accumulated_data['decision'] = result.get('decision', {})
                    
                    success = True
                    self.logger.info(f"Successfully completed agent: {agent_name}")
                    
                except asyncio.TimeoutError:
                    self.logger.error(f"Timeout in agent {agent_name} (attempt {attempt + 1})")
                    attempt += 1
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(RETRY_DELAY)
                        
                except Exception as e:
                    self.logger.error(f"Error in agent {agent_name}: {e} (attempt {attempt + 1})")
                    attempt += 1
                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(RETRY_DELAY)
            
            if not success:
                self.logger.error(f"All retries failed for agent: {agent_name}")
                # We'll continue with the next agent, but store the failure
                cycle_results[agent_name] = {
                    "status": "failed", 
                    "error": f"Failed after {MAX_RETRIES} attempts"
                }
        
        # Log results
        if ENABLE_LOGGING:
            await self._log_results(cycle_results)
        
        return cycle_results
    
    async def _log_results(self, cycle_results: Dict):
        """Log the results to database and/or markdown."""
        timestamp = datetime.now().isoformat()
        
        # Log to database if enabled
        if LOG_TO_DATABASE:
            await self._log_to_database(timestamp, cycle_results)
        
        # Log to markdown if enabled
        if LOG_TO_MARKDOWN:
            await self._log_to_markdown(timestamp, cycle_results)
    
    async def _log_to_database(self, timestamp: str, cycle_results: Dict):
        """Log results to database."""
        try:
            # Placeholder for database logging
            # Implementation would depend on the database system used
            self.logger.info(f"Logging results to database at {timestamp}")
            # TODO: Implement actual database logging
        except Exception as e:
            self.logger.error(f"Error logging to database: {e}")
    
    async def _log_to_markdown(self, timestamp: str, cycle_results: Dict):
        """Log results to markdown file."""
        try:
            filename = f"trading_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            with open(filename, 'w') as f:
                f.write(f"# Trading Cycle Log - {timestamp}\n\n")
                
                f.write("## Cycle Results\n")
                for agent_name, result in cycle_results.items():
                    status = result.get("status", "unknown")
                    f.write(f"### {agent_name.replace('_', ' ').title()}\n")
                    f.write(f"- Status: {status}\n")
                    if "error" in result:
                        f.write(f"- Error: {result['error']}\n")
                    f.write("\n")
            
            self.logger.info(f"Results logged to markdown: {filename}")
        except Exception as e:
            self.logger.error(f"Error logging to markdown: {e}")
    
    async def run_continuous_cycle(self):
        """Run the trading cycle continuously at intervals."""
        self.logger.info("Starting continuous trading cycle...")
        
        while True:
            try:
                start_time = time.time()
                self.logger.info("Starting new trading cycle")
                
                cycle_results = await self.run_single_cycle()
                
                elapsed_time = time.time() - start_time
                self.logger.info(f"Trading cycle completed in {elapsed_time:.2f}s")
                
                # Wait for the next cycle
                sleep_time = max(0, TRADING_CYCLE_INTERVAL - elapsed_time)
                self.logger.info(f"Waiting {sleep_time:.2f}s until next cycle")
                await asyncio.sleep(sleep_time)
                
            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal, stopping orchestrator")
                break
            except Exception as e:
                self.logger.error(f"Error in continuous cycle: {e}")
                await asyncio.sleep(10)  # Wait before restarting
    
    def get_status(self) -> Dict[str, str]:
        """Get the current status of all agents."""
        status = {}
        for agent_name in AGENT_ORDER:
            if agent_name in self.agents:
                status[agent_name] = "initialized"
            else:
                status[agent_name] = "not initialized"
        return status


async def main():
    """Main entry point for the orchestrator."""
    orchestrator = TradingOrchestrator()
    
    print("Trading Orchestrator initialized")
    print("Agents status:", orchestrator.get_status())
    print("Starting continuous trading cycle...")
    
    try:
        await orchestrator.run_continuous_cycle()
    except KeyboardInterrupt:
        print("\nShutting down orchestrator...")
    

if __name__ == "__main__":
    asyncio.run(main())