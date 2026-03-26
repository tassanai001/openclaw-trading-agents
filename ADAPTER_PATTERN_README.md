# Exchange Adapter Pattern

Implementation of the Adapter Pattern for OpenClaw Trading Agents, supporting multiple exchanges through a unified interface.

## 🎯 Overview

This refactor introduces an adapter pattern that allows the trading system to:
- Support multiple exchanges (Binance, Hyperliquid) through a unified interface
- Easily add new exchanges in the future
- Maintain backward compatibility with existing orchestrator code
- Switch between exchanges via configuration

## 📁 File Structure

```
agents/execution/
├── execution_agent.py          # Main agent (adapter-aware)
├── execution.py                # Legacy agent (keep for backward compat)
├── config.py                   # Execution configuration
├── hyperliquid_api.py          # Original Hyperliquid API wrapper
├── adapters/                   # NEW: Exchange adapters
│   ├── __init__.py
│   ├── base.py                 # Abstract base class (interface)
│   ├── binance.py              # Binance Spot Testnet adapter
│   └── hyperliquid.py          # Hyperliquid Testnet adapter
└── models/                     # NEW: Shared data models
    ├── __init__.py
    ├── common.py               # Enums, credentials
    ├── order.py                # Order, OrderResult
    └── position.py             # Position, Balance
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Select active exchange
ACTIVE_EXCHANGE=binance  # or "hyperliquid"

# Binance Spot Testnet
BINANCE_TESTNET=true
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret

# Hyperliquid Testnet
HYPERLIQUID_API_KEY=your_testnet_key
HYPERLIQUID_API_SECRET=your_testnet_secret
```

### Get Binance Testnet Credentials

1. Visit: https://testnet.binance.vision/
2. Click "Generate HMAC_SHA256 Key"
3. Copy API Key and Secret Key
4. Add to your `.env` file

## 🚀 Usage

### Basic Usage

```python
from agents.execution.execution_agent import ExecutionAgent

# Create agent for Binance
agent = ExecutionAgent(exchange="binance")

# Initialize
await agent.initialize()

# Get balance
balance = await agent.get_balance()
print(f"Balance: ${balance.total_balance}")

# Get price
price = await agent.get_ticker_price("BTCUSDT")
print(f"BTC Price: ${price}")

# Place order
result = await agent.place_order(
    asset="BTC",
    side="B",  # Buy
    leverage=1,
    order_type="market",
    size=0.001
)

if result.success:
    print(f"Order placed: {result.order_id}")
else:
    print(f"Order failed: {result.message}")

# Cleanup
await agent.close()
```

### Switching Exchanges

```python
# Use Binance
binance_agent = ExecutionAgent(exchange="binance")
await binance_agent.initialize()

# Use Hyperliquid
hyperliquid_agent = ExecutionAgent(exchange="hyperliquid")
await hyperliquid_agent.initialize()
```

### Paper Trading Mode

```python
from agents.execution.config import ExecutionConfig
from config.paper_trading_config import PaperTradingConfig

config = ExecutionConfig(paper_trading=True)
paper_config = PaperTradingConfig(initial_balance=10000.0)

agent = ExecutionAgent(
    exchange="binance",
    config=config,
    paper_trading_config=paper_config
)

await agent.initialize()
# All trades will be simulated
```

## 🧪 Testing

### Run Adapter Tests

```bash
# Test Binance adapter
cd /Users/nunamzza/projects/trading/openclaw-trading-agents
python3 tests/adapters/test_adapter_pattern.py

# Run pytest
pytest tests/adapters/ -v
```

### Test Individual Components

```python
# Test balance
python3 -c "
from agents.execution.execution_agent import ExecutionAgent
import asyncio
agent = ExecutionAgent('binance')
asyncio.run(agent.initialize())
balance = asyncio.run(agent.get_balance())
print(f'Balance: \${balance.total_balance}')
asyncio.run(agent.close())
"

# Test price feed
python3 -c "
from agents.execution.execution_agent import ExecutionAgent
import asyncio
agent = ExecutionAgent('binance')
asyncio.run(agent.initialize())
price = asyncio.run(agent.get_ticker_price('BTCUSDT'))
print(f'BTC Price: \${price}')
asyncio.run(agent.close())
"
```

## 📊 Adapter Interface

All adapters implement the `ExchangeAdapter` base class:

```python
class ExchangeAdapter(ABC):
    async def initialize(self) -> bool: ...
    async def place_order(self, order: Order) -> OrderResult: ...
    async def cancel_order(self, symbol: str, order_id: str) -> bool: ...
    async def get_open_orders(self, symbol: str = None) -> List[Order]: ...
    async def get_position(self, symbol: str) -> Optional[Position]: ...
    async def get_positions(self) -> List[Position]: ...
    async def get_balance(self) -> Balance: ...
    async def get_ticker_price(self, symbol: str) -> float: ...
    def get_symbol_info(self, symbol: str) -> dict: ...
    @property
    def name(self) -> str: ...
```

## 🆕 Adding a New Exchange

To add a new exchange (e.g., Kraken):

1. **Create adapter file**: `agents/execution/adapters/kraken.py`

```python
from .base import ExchangeAdapter
from ..models.order import Order, OrderResult
from ..models.position import Position, Balance

class KrakenAdapter(ExchangeAdapter):
    @property
    def name(self) -> str:
        return "Kraken"
    
    async def initialize(self) -> bool:
        # Initialize Kraken client
        pass
    
    async def place_order(self, order: Order) -> OrderResult:
        # Implement order placement
        pass
    
    # ... implement all other methods
```

2. **Update adapters __init__.py**:
```python
from .kraken import KrakenAdapter
__all__ = ["ExchangeAdapter", "BinanceAdapter", "HyperliquidAdapter", "KrakenAdapter"]
```

3. **Update execution_agent.py**:
```python
if self.exchange == "kraken":
    self.adapter = KrakenAdapter(self.credentials)
```

4. **Add credentials to .env**:
```bash
KRAKEN_API_KEY=your_key
KRAKEN_API_SECRET=your_secret
```

## ⚠️ Important Notes

### Testnet Only
- **Binance**: Uses Spot Testnet (https://testnet.binance.vision)
- **Hyperliquid**: Uses Testnet (https://api.hyperliquid-testnet.xyz)
- **NO REAL MONEY** is traded unless you explicitly change configuration

### Minimum Order Sizes
- **Binance**: Minimum ~$10 USDT per order
- **Hyperliquid**: Minimum ~$5 USDT per order

### Rate Limits
- **Binance Testnet**: 1200 requests/minute
- **Hyperliquid Testnet**: Standard limits apply

### Symbol Format
- Adapters normalize symbol formats:
  - Input: `"BTC"` or `"BTCUSDT"` → Internal: `"BTCUSDT"`
  - Hyperliquid internally uses `"BTC"` but adapter handles conversion

## 🔍 Troubleshooting

### Import Errors
```bash
# Install dependencies
pip3 install python-binance==1.0.19 websockets==12.0
```

### Connection Failed
- Check API credentials in `.env`
- Verify testnet endpoint is accessible
- Check firewall/network settings

### Order Rejected
- Verify minimum order size ($10 for Binance)
- Check symbol format (BTCUSDT, not BTC/USDT)
- Ensure sufficient balance

## 📝 Migration Notes

### From Legacy execution.py

The new `execution_agent.py` maintains backward compatibility:

```python
# Old way (still works)
from agents.execution.execution import ExecutionAgent

# New way (recommended)
from agents.execution.execution_agent import ExecutionAgent
agent = ExecutionAgent(exchange="binance")
```

### API Compatibility

All existing methods are preserved:
- `place_order()` ✅
- `cancel_order()` ✅
- `get_open_orders()` ✅
- `get_account_info()` ✅
- `execute_signal()` ✅
- `execute_from_signal()` ✅

## 🎯 Next Steps

1. **Set up credentials**: Add Binance/Hyperliquid testnet keys to `.env`
2. **Run tests**: Verify adapters work with `python3 tests/adapters/test_adapter_pattern.py`
3. **Update orchestrator**: Modify orchestrator to pass `exchange` parameter
4. **Monitor**: Watch first few trading cycles to ensure smooth operation

## 📚 References

- [Binance Testnet](https://testnet.binance.vision/)
- [Binance API Docs](https://binance-docs.github.io/apidocs/spot/en/)
- [Hyperliquid Testnet](https://hyperliquid-testnet.xyz/)
- [python-binance SDK](https://github.com/sammchardy/python-binance)
