# Quick Start Guide - Binance Adapter

Get up and running with the new Binance adapter in 5 minutes!

---

## ⚡ 3-Step Setup

### Step 1: Get Binance Testnet Credentials (2 min)

1. Visit: https://testnet.binance.vision/
2. Click **"Generate HMAC_SHA256 Key"**
3. Copy the **API Key** and **Secret Key**
4. Save them somewhere safe

### Step 2: Configure Environment (1 min)

```bash
cd /Users/nunamzza/projects/trading/openclaw-trading-agents

# Copy example and edit
cp .env.example .env
nano .env
```

Add these lines:
```bash
ACTIVE_EXCHANGE=binance
BINANCE_TESTNET=true
BINANCE_API_KEY=YOUR_API_KEY_HERE
BINANCE_API_SECRET=YOUR_SECRET_HERE
```

### Step 3: Test Connection (2 min)

```bash
# Install dependencies (if not done)
pip3 install python-binance==1.0.19 websockets==12.0

# Run quick test
python3 << 'EOF'
import asyncio
from agents.execution.execution_agent import ExecutionAgent

async def test():
    agent = ExecutionAgent(exchange="binance")
    
    # Initialize
    print("Connecting to Binance Testnet...")
    success = await agent.initialize()
    
    if success:
        print("✅ Connected!")
        
        # Get balance
        balance = await agent.get_balance()
        print(f"💰 Balance: ${balance.total_balance:.2f}")
        
        # Get BTC price
        price = await agent.get_ticker_price("BTCUSDT")
        print(f"₿ BTC Price: ${price:.2f}")
        
        await agent.close()
        print("✅ Test complete!")
    else:
        print("❌ Connection failed - check credentials")

asyncio.run(test())
EOF
```

---

## 🎯 That's It!

Your bot is now configured to use Binance Spot Testnet!

### What Happens Next

- **Existing bot**: Will use Binance instead of Hyperliquid (if you updated orchestrator)
- **Manual testing**: Use the test script above
- **Production**: Bot runs every 5 minutes as before

---

## 🧪 Quick Tests

### Test Balance
```bash
python3 -c "
import asyncio
from agents.execution.execution_agent import ExecutionAgent
agent = ExecutionAgent('binance')
async def t():
    await agent.initialize()
    b = await agent.get_balance()
    print(f'Balance: \${b.total_balance}')
    await agent.close()
asyncio.run(t())
"
```

### Test Price Feed
```bash
python3 -c "
import asyncio
from agents.execution.execution_agent import ExecutionAgent
agent = ExecutionAgent('binance')
async def t():
    await agent.initialize()
    p = await agent.get_ticker_price('BTCUSDT')
    print(f'BTC: \${p}')
    await agent.close()
asyncio.run(t())
"
```

### Place Test Order (Market Buy - Small)
```bash
python3 -c "
import asyncio
from agents.execution.execution_agent import ExecutionAgent
agent = ExecutionAgent('binance')
async def t():
    await agent.initialize()
    result = await agent.place_order('BTC', 'B', 1, 'market', size=0.0002)
    print(f'Order: {\"✅ Success\" if result.success else \"❌ Failed\"}')
    if result.success:
        print(f'ID: {result.order_id}')
        print(f'Filled: {result.filled_quantity} @ {result.filled_price}')
    await agent.close()
asyncio.run(t())
"
```

---

## 🔄 Switch Back to Hyperliquid

Just change `.env`:
```bash
ACTIVE_EXCHANGE=hyperliquid
```

No code changes needed!

---

## ⚠️ Important

- **Testnet only** - No real money
- **Min order**: ~$10 USDT on Binance
- **Keep credentials secret** - Don't commit .env to git

---

## 📚 More Info

- **Full docs**: `ADAPTER_PATTERN_README.md`
- **Implementation**: `IMPLEMENTATION_SUMMARY.md`
- **Refactor plan**: `REFACTOR_BINANCE_ADAPTER.md`

---

## 🆘 Troubleshooting

**"Module not found"**
```bash
pip3 install python-binance==1.0.19 websockets==12.0
```

**"Connection failed"**
- Check API keys in `.env`
- Make sure `BINANCE_TESTNET=true`
- Verify testnet is accessible: https://testnet.binance.vision/

**"Order rejected"**
- Minimum order is ~$10
- Use format: `BTCUSDT` (not BTC/USDT)
- Check you have sufficient balance

---

**Happy Trading! 🚀**
