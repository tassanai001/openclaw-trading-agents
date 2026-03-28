#!/usr/bin/env python3
"""Check Hyperliquid Testnet Wallet Balance"""

import sys
import os
sys.path.insert(0, '.')

from hyperliquid.info import Info
from eth_account import Account

# Load from .env
api_key = os.getenv("HYPERLIQUID_API_KEY")
api_secret = os.getenv("HYPERLIQUID_API_SECRET")

if not api_key:
    print("❌ HYPERLIQUID_API_KEY not configured in .env")
    sys.exit(1)

if not api_secret:
    print("❌ HYPERLIQUID_API_SECRET not configured in .env")
    sys.exit(1)

print("=" * 60)
print("🔍 Hyperliquid Testnet Wallet Balance Check")
print("=" * 60)

print(f"\n📋 Wallet Info:")
print(f"   Address: {api_key}")

# Verify private key matches address
wallet = Account.from_key(api_secret)
print(f"   From Private Key: {wallet.address}")

if wallet.address.lower() == api_key.lower():
    print(f"   ✅ Private Key matches Wallet Address")
else:
    print(f"   ❌ WARNING: Private Key does NOT match Wallet Address!")
    print(f"      Expected: {api_key}")
    print(f"      Got: {wallet.address}")

# Get balance
print(f"\n💰 Checking Balance...")
try:
    info = Info(base_url="https://api.hyperliquid-testnet.xyz")
    data = info.user_state(api_key)
    
    margin_summary = data.get("marginSummary", {})
    account_value = margin_summary.get("accountValue", "0")
    total_raw_usd = margin_summary.get("totalRawUsd", "0")
    total_margin_used = margin_summary.get("totalMarginUsed", "0")
    
    print(f"\n✅ Balance Retrieved Successfully!")
    print(f"\n📊 Account Summary:")
    print(f"   Account Value: ${account_value}")
    print(f"   Available USDC: ${total_raw_usd}")
    print(f"   Margin Used: ${total_margin_used}")
    
    # Check positions
    positions = data.get("assetPositions", [])
    print(f"\n📈 Active Positions: {len(positions)}")
    for pos in positions:
        print(f"   - {pos}")
    
    # Check if balance is sufficient for trading
    try:
        balance_float = float(account_value)
        print(f"\n⚡ Trading Status:")
        if balance_float <= 0:
            print(f"   ❌ No balance - Must claim USDC first!")
            print(f"   👉 https://app.hyperliquid-testnet.xyz/drip")
        elif balance_float < 10:
            print(f"   ⚠️  Low balance (${balance_float:.2f}) - Minimum ~$10 recommended")
            print(f"   👉 https://app.hyperliquid-testnet.xyz/drip")
        else:
            print(f"   ✅ Balance OK - Ready to trade!")
    except:
        pass
        
except Exception as e:
    print(f"\n❌ Error checking balance: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
