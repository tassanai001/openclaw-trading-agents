#!/usr/bin/env python3
"""Run scanner agent and generate market report"""
import asyncio
import sys
from datetime import datetime
from agents.scanner.scanner import Scanner

async def main():
    scanner = Scanner()
    results = await scanner.scan_market()
    
    # Print summary
    print(f"\n=== Market Scan Complete: {datetime.now().isoformat()} ===\n")
    
    for pair, timeframes in results.items():
        print(f"\n{pair}:")
        for tf, data in timeframes.items():
            if 'signal' in data:
                print(f"  {tf}: {data['signal']}")
            else:
                print(f"  {tf}: ERROR - {data.get('error', 'Unknown')}")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
    sys.exit(0)
