#!/usr/bin/env python3
"""
Test script for Binance Demo Mode connection

This script verifies:
1. Connection to demo-api.binance.com
2. Account balance query
3. Market price retrieval
4. Test order placement

Requirements: python-binance >= 1.0.20
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Get credentials from environment
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')
DEMO_MODE = os.getenv('BINANCE_DEMO_MODE', 'false').lower() == 'true'
TESTNET = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'


async def test_demo_connection():
    """Test Binance Demo Mode connection"""
    from binance import AsyncClient
    
    print("=" * 60)
    print("Binance Demo Mode Connection Test")
    print("=" * 60)
    print(f"Demo Mode: {DEMO_MODE}")
    print(f"Testnet: {TESTNET}")
    print(f"API Key: {API_KEY[:20]}...")
    print("=" * 60)
    
    # Initialize client
    if DEMO_MODE:
        client = AsyncClient(
            api_key=API_KEY,
            api_secret=API_SECRET,
            demo=True
        )
        mode_name = "DEMO MODE"
    elif TESTNET:
        client = AsyncClient(
            api_key=API_KEY,
            api_secret=API_SECRET,
            testnet=True
        )
        mode_name = "TESTNET"
    else:
        client = AsyncClient(
            api_key=API_KEY,
            api_secret=API_SECRET
        )
        mode_name = "MAINNET"
    
    print(f"\n📡 Connecting to Binance ({mode_name})...")
    
    try:
        # Test 1: Ping
        print("\n[Test 1] API Ping...")
        ping = await client.ping()
        print(f"✅ Ping successful: {ping}")
        
        # Test 2: Server Time
        print("\n[Test 2] Server Time...")
        server_time = await client.get_server_time()
        print(f"✅ Server time: {server_time['serverTime']}")
        
        # Test 3: Account Info
        print("\n[Test 3] Account Information...")
        account = await client.get_account()
        print(f"✅ Account connected!")
        print(f"   Maker Commission: {account['makerCommission']}")
        print(f"   Taker Commission: {account['takerCommission']}")
        
        # Show non-zero balances
        non_zero_balances = [
            b for b in account['balances'] 
            if float(b['free']) > 0 or float(b['locked']) > 0
        ]
        print(f"   Non-zero balances: {len(non_zero_balances)}")
        for bal in non_zero_balances[:10]:  # Show first 10
            if float(bal['free']) > 0 or float(bal['locked']) > 0:
                print(f"   - {bal['asset']}: {bal['free']} (locked: {bal['locked']})")
        
        # Test 4: Market Prices
        print("\n[Test 4] Market Prices...")
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        for symbol in symbols:
            ticker = await client.get_symbol_ticker(symbol=symbol)
            print(f"✅ {symbol}: ${float(ticker['price']):,.2f}")
        
        # Test 5: Get Open Orders (should be empty for fresh account)
        print("\n[Test 5] Open Orders...")
        open_orders = await client.get_open_orders()
        print(f"✅ Open orders: {len(open_orders)}")
        
        # Test 6: Try to place a test order (will fail with insufficient balance for real trading)
        print("\n[Test 6] Test Order Placement...")
        try:
            # Try to place a small market order (will likely fail due to min notional)
            order = await client.create_order(
                symbol='BTCUSDT',
                side='BUY',
                type='MARKET',
                quantity=0.0001  # Very small amount
            )
            print(f"✅ Order placed: {order['orderId']}")
            print(f"   Status: {order['status']}")
            print(f"   Filled: {order['executedQty']}")
        except Exception as e:
            # Expected to fail if insufficient balance or min notional
            error_msg = str(e)
            if 'Insufficient balance' in error_msg or 'MIN_NOTIONAL' in error_msg:
                print(f"✅ Order rejected as expected: {error_msg[:100]}")
                print("   (This is normal for demo accounts with limited balance)")
            else:
                print(f"⚠️  Order failed: {error_msg[:100]}")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Demo Mode is working correctly!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await client.close_connection()


async def test_with_adapter():
    """Test using the BinanceAdapter class"""
    print("\n" + "=" * 60)
    print("Testing with BinanceAdapter Class")
    print("=" * 60)
    
    from agents.execution.models.common import ExchangeCredentials
    from agents.execution.adapters.binance import BinanceAdapter
    
    # Create credentials
    credentials = ExchangeCredentials(
        api_key=API_KEY,
        api_secret=API_SECRET,
        testnet=TESTNET,
        demo_mode=DEMO_MODE
    )
    
    # Create adapter
    adapter = BinanceAdapter(credentials)
    
    # Initialize
    print("\n📡 Initializing adapter...")
    success = await adapter.initialize()
    
    if not success:
        print("❌ Adapter initialization failed")
        return False
    
    try:
        # Test balance
        print("\n[Test] Getting balance...")
        balance = await adapter.get_balance()
        print(f"✅ Total balance: ${balance.total_balance:,.2f} {balance.currency}")
        print(f"   Available: ${balance.available_balance:,.2f}")
        
        # Test ticker
        print("\n[Test] Getting BTCUSDT price...")
        price = await adapter.get_ticker_price('BTCUSDT')
        print(f"✅ BTCUSDT: ${price:,.2f}")
        
        print("\n✅ Adapter tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Adapter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await adapter.close()


async def main():
    """Run all tests"""
    print("\n🚀 Starting Binance Demo Mode Tests\n")
    
    # Test 1: Direct client connection
    result1 = await test_demo_connection()
    
    # Test 2: Adapter pattern
    if result1:
        result2 = await test_with_adapter()
        return result1 and result2
    
    return result1


if __name__ == '__main__':
    success = asyncio.run(main())
    exit(0 if success else 1)
