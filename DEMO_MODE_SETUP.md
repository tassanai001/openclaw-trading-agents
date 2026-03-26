# Binance Demo Mode Setup Guide

## ✅ Working Solution

This guide explains how to connect to **Binance Spot Demo Mode** (NOT Testnet) using the official Demo API.

---

## 🔍 Root Cause Analysis

### Problem Summary
We were unable to connect to `https://demo-api.binance.com` using `python-binance==1.0.19` due to:

1. **Missing `demo` parameter**: Version 1.0.19 doesn't support the `demo=True` parameter
2. **URL mangling with `base_endpoint`**: When passing `base_endpoint='demo-api.binance.com'`, the library incorrectly transformed it to `apidemo-api.binance.com.binance.com`
3. **SSL certificate errors**: The mangled URL caused hostname mismatches in SSL verification

### Why It Failed

The `python-binance` library constructs URLs like this:
```python
API_URL = "https://api{}.binance.{}/api"
# With base_endpoint='demo-api.binance.com' and tld='com':
# Results in: https://api{demo-api.binance.com}.binance.com/api
# Which becomes: https://apidemo-api.binance.com.binance.com/api ❌
```

### The Fix

**Upgrade to `python-binance>=1.0.20`** which added native Demo Mode support via the `demo=True` parameter:

```python
# ✅ Correct way (requires v1.0.20+)
client = AsyncClient(
    api_key=API_KEY,
    api_secret=API_SECRET,
    demo=True  # Automatically uses https://demo-api.binance.com
)
```

---

## 📦 Installation

### 1. Upgrade python-binance

```bash
cd /Users/nunamzza/projects/trading/openclaw-trading-agents
pip3 install --upgrade "python-binance>=1.0.20"
```

**Current version installed:** `1.0.36` ✅

### 2. Verify Installation

```bash
python3 -c "from binance import AsyncClient; import inspect; print('demo' in inspect.signature(AsyncClient.__init__).parameters)"
# Should print: True
```

---

## 🔑 API Key Setup

### Get Demo Mode API Keys

1. Go to **Binance Demo Trading**: https://demo.binance.com/
2. Log in with your Binance account
3. Navigate to **API Management**: https://demo.binance.com/en/my/settings/api-management
4. Create a new API key with:
   - ✅ Enable Reading
   - ✅ Enable Spot & Margin Trading
   - ❌ Disable Withdrawals (security best practice)

### Configure Environment

Edit `.env`:

```bash
# Binance Spot Demo Mode (Official Demo API)
BINANCE_DEMO_MODE=true
BINANCE_TESTNET=false
BINANCE_API_KEY=your_demo_api_key
BINANCE_API_SECRET=your_demo_secret
```

---

## 🧪 Testing Connection

### Run Test Script

```bash
cd /Users/nunamzza/projects/trading/openclaw-trading-agents
python3 test_demo_connection.py
```

**Expected output:**
```
✅ Ping successful: {}
✅ Account connected!
   Non-zero balances: 4
   - BTC: 0.05000000
   - ETH: 1.00000000
   - BNB: 2.00000000
   - USDT: 5000.00000000
✅ BTCUSDT: $69,422.97
✅ ALL TESTS PASSED - Demo Mode is working correctly!
```

### Manual Test with curl

```bash
# Test public endpoint (no auth required)
curl "https://demo-api.binance.com/api/v3/ping"
# Returns: {}

# Test authenticated endpoint
curl -X GET "https://demo-api.binance.com/api/v3/account" \
  -H "X-MBX-APIKEY: YOUR_API_KEY"
# Returns account info with signature error (expected without signature)
```

---

## 📊 Demo Mode vs Testnet

| Feature | Demo Mode | Testnet |
|---------|-----------|---------|
| **URL** | `https://demo-api.binance.com` | `https://testnet.binance.vision` |
| **Market Data** | Real market data from mainnet | Simulated/independent data |
| **Balances** | Persistent (reset manually) | Reset monthly |
| **Features** | Same as mainnet | May have upcoming features |
| **API Keys** | From demo.binance.com | From testnet.binance.vision |
| **Best For** | Realistic strategy testing | Integration testing |

### When to Use Demo Mode

✅ You want **realistic market data** (live prices, order books)
✅ You want to test with **persistent demo balances**
✅ You want to validate strategies against **real market conditions**

### When to Use Testnet

✅ You need to test **upcoming features** before mainnet release
✅ You want **monthly balance resets**
✅ You're doing **integration testing** with separate environment

---

## 🔧 Code Examples

### Using AsyncClient Directly

```python
from binance import AsyncClient
import asyncio

async def main():
    # Demo Mode
    client = AsyncClient(
        api_key='YOUR_API_KEY',
        api_secret='YOUR_SECRET',
        demo=True
    )
    
    # Get account info
    account = await client.get_account()
    print(f"Balances: {account['balances']}")
    
    # Get price
    ticker = await client.get_symbol_ticker(symbol='BTCUSDT')
    print(f"BTC Price: {ticker['price']}")
    
    # Place order
    order = await client.create_order(
        symbol='BTCUSDT',
        side='BUY',
        type='MARKET',
        quantity=0.001
    )
    print(f"Order: {order}")
    
    await client.close_connection()

asyncio.run(main())
```

### Using BinanceAdapter

```python
from agents.execution.models.common import ExchangeCredentials
from agents.execution.adapters.binance import BinanceAdapter

# Create credentials with demo_mode=True
credentials = ExchangeCredentials(
    api_key='YOUR_API_KEY',
    api_secret='YOUR_SECRET',
    testnet=False,
    demo_mode=True
)

# Initialize adapter
adapter = BinanceAdapter(credentials)
await adapter.initialize()

# Get balance
balance = await adapter.get_balance()
print(f"Total: ${balance.total_balance}")

# Get price
price = await adapter.get_ticker_price('BTCUSDT')
print(f"BTC: ${price}")

# Place order
from agents.execution.models.order import Order, OrderSide, OrderType
order = Order(
    symbol='BTCUSDT',
    side=OrderSide.BUY,
    type=OrderType.MARKET,
    quantity=0.001
)
result = await adapter.place_order(order)
print(f"Order result: {result}")

await adapter.close()
```

---

## 🐛 Troubleshooting

### Error: `TypeError: __init__() got an unexpected keyword argument 'demo'`

**Cause:** Using old version of python-binance (< 1.0.20)

**Fix:**
```bash
pip3 install --upgrade "python-binance>=1.0.20"
```

### Error: `SSLCertVerificationError: Hostname mismatch`

**Cause:** Using `base_endpoint` parameter incorrectly

**Fix:** Use `demo=True` instead of manually setting `base_endpoint`

```python
# ❌ Wrong
client = AsyncClient(api_key=KEY, api_secret=SECRET, base_endpoint='demo-api.binance.com')

# ✅ Correct
client = AsyncClient(api_key=KEY, api_secret=SECRET, demo=True)
```

### Error: `Mandatory parameter 'signature' was not sent`

**Cause:** Trying to access private endpoints without proper authentication

**Fix:** Ensure you're using the AsyncClient with correct API key/secret, the library handles signatures automatically.

### Error: `Insufficient balance`

**Cause:** Demo account has limited balance

**Fix:** 
1. Reset balance via Demo Trading UI: https://demo.binance.com/
2. Or use smaller order sizes (min notional is ~$10 USDT)

---

## 📝 Files Modified

1. **`agents/execution/adapters/binance.py`**
   - Updated to use `demo=True` parameter
   - Added proper initialization for Demo/Testnet/Mainnet modes

2. **`requirements.txt`**
   - Changed from `python-binance==1.0.19` to `python-binance>=1.0.20`

3. **`.env`**
   - Set `BINANCE_DEMO_MODE=true`
   - Set `BINANCE_TESTNET=false`

4. **`test_demo_connection.py`** (new)
   - Comprehensive test script for Demo Mode

---

## ✅ Success Criteria Checklist

- [x] Can connect to `https://demo-api.binance.com` without SSL errors
- [x] Can query account balance (returns demo balances)
- [x] Can get market prices (BTCUSDT, ETHUSDT, BNBUSDT)
- [x] Can place test orders (executes successfully)
- [x] Authentication works correctly

---

## 🔗 References

- **Binance Demo Mode Docs**: https://developers.binance.com/docs/binance-spot-api-docs/demo-mode/general-info
- **Demo Trading UI**: https://demo.binance.com/
- **python-binance GitHub**: https://github.com/sammchardy/python-binance
- **python-binance PyPI**: https://pypi.org/project/python-binance/

---

## 📞 Support

If you encounter issues:

1. Check that `python-binance>=1.0.20` is installed
2. Verify API keys are from **demo.binance.com** (not testnet or mainnet)
3. Run `python3 test_demo_connection.py` to diagnose
4. Check Binance Demo Mode announcements for maintenance

**Last Updated:** 2026-03-26
**Tested With:** python-binance 1.0.36
