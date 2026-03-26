#!/usr/bin/env python3
"""
Run Scanner Agent Only
"""
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.scanner.scanner import Scanner


async def main():
    print(f"🔍 Scanner Agent Run - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ICT")
    print("=" * 60)
    
    scanner = Scanner()
    results = await scanner.scan_market()
    
    print("\n📊 SCAN RESULTS SUMMARY")
    print("=" * 60)
    
    for pair, timeframes in results.items():
        print(f"\n{pair}:")
        for tf, data in timeframes.items():
            if "error" not in data:
                signal = data.get("signal", "UNKNOWN")
                print(f"  {tf}: {signal}")
            else:
                print(f"  {tf}: ERROR - {data['error']}")
    
    print("\n" + "=" * 60)
    print(f"Scan completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ICT")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
