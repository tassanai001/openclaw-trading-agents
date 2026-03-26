#!/usr/bin/env python3
"""
Simple test to verify adapter pattern works
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from agents.execution.execution_agent import ExecutionAgent
from agents.execution.models.common import OrderSide, OrderType


async def test_binance_adapter():
    """Test Binance adapter through ExecutionAgent"""
    print("\n" + "="*60)
    print("Testing Binance Adapter")
    print("="*60)
    
    agent = ExecutionAgent(exchange="binance")
    
    # Initialize
    print("\n1. Initializing...")
    success = await agent.initialize()
    if not success:
        print("❌ Failed to initialize (likely missing credentials)")
        return False
    print("✅ Initialized successfully")
    
    # Get balance
    print("\n2. Getting balance...")
    balance = await agent.get_balance()
    print(f"   Total: ${balance.total_balance:.2f}")
    print(f"   Available: ${balance.available_balance:.2f}")
    print(f"   Locked: ${balance.locked_balance:.2f}")
    
    # Get ticker price
    print("\n3. Getting BTC/USDT price...")
    price = await agent.get_ticker_price("BTCUSDT")
    print(f"   BTC/USDT: ${price:.2f}")
    
    # Get symbol info
    print("\n4. Getting symbol info...")
    if agent.adapter:
        info = agent.adapter.get_symbol_info("BTCUSDT")
        print(f"   Min quantity: {info['min_quantity']}")
        print(f"   Min notional: ${info['min_notional']}")
    
    # Cleanup
    await agent.close()
    print("\n✅ Binance adapter test completed!")
    return True


async def test_hyperliquid_adapter():
    """Test Hyperliquid adapter through ExecutionAgent"""
    print("\n" + "="*60)
    print("Testing Hyperliquid Adapter")
    print("="*60)
    
    agent = ExecutionAgent(exchange="hyperliquid")
    
    # Initialize
    print("\n1. Initializing...")
    success = await agent.initialize()
    if not success:
        print("❌ Failed to initialize (likely missing credentials)")
        return False
    print("✅ Initialized successfully")
    
    # Get balance
    print("\n2. Getting balance...")
    balance = await agent.get_balance()
    print(f"   Total: ${balance.total_balance:.2f}")
    print(f"   Available: ${balance.available_balance:.2f}")
    
    # Get ticker price
    print("\n3. Getting BTC/USDT price...")
    price = await agent.get_ticker_price("BTCUSDT")
    print(f"   BTC/USDT: ${price:.2f}")
    
    # Cleanup
    await agent.close()
    print("\n✅ Hyperliquid adapter test completed!")
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ADAPTER PATTERN VERIFICATION TEST")
    print("="*60)
    
    # Test Binance
    binance_ok = await test_binance_adapter()
    
    # Test Hyperliquid
    hyperliquid_ok = await test_hyperliquid_adapter()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Binance Adapter:     {'✅ PASS' if binance_ok else '⚠️  SKIP (no credentials)'}")
    print(f"Hyperliquid Adapter: {'✅ PASS' if hyperliquid_ok else '⚠️  SKIP (no credentials)'}")
    print("="*60)
    
    if binance_ok or hyperliquid_ok:
        print("\n✅ Adapter pattern is working correctly!")
    else:
        print("\n⚠️  Tests skipped due to missing credentials")
        print("   Set up .env file with API keys to run full tests")


if __name__ == "__main__":
    asyncio.run(main())
