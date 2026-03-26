#!/usr/bin/env python3
"""
Scanner Agent Runner with Direct Telegram API
- สแกนตลาดและส่งสัญญาณผ่าน Telegram โดยตรง
- ไม่พึ่งพา OpenClaw delivery
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.scanner.scanner import Scanner
from agents.scanner.config import get_pairs
from config.telegram_bot import (
    send_startup_notification,
    send_signal_alert,
    send_message,
    send_error_alert
)


async def generate_scanner_summary(results: dict) -> str:
    """สร้างสรุปผลการสแกนสำหรับ Telegram"""
    timestamp = datetime.now().strftime('%H:%M')
    
    buy_count = 0
    sell_count = 0
    hold_count = 0
    error_count = 0
    
    signals_by_pair = {}
    
    for pair, timeframes in results.items():
        pair_signals = []
        for tf, data in timeframes.items():
            if "error" in data:
                error_count += 1
                pair_signals.append(f"{tf}: ❌")
            else:
                signal = data.get("signal", "HOLD")
                if signal == "BUY":
                    buy_count += 1
                    pair_signals.append(f"{tf}: 🟢")
                elif signal == "SELL":
                    sell_count += 1
                    pair_signals.append(f"{tf}: 🔴")
                else:
                    hold_count += 1
                    pair_signals.append(f"{tf}: ⚪")
        
        signals_by_pair[pair] = pair_signals
    
    # สร้างข้อความสรุป
    summary = f"""🔍 <b>Scanner Agent Summary</b> ({timestamp})

<b>สถานะ:</b> ✅ สำเร็จ

<b>สัญญาณที่พบ:</b>
• 🟢 BUY: {buy_count}
• 🔴 SELL: {sell_count}
• ⚪ HOLD: {hold_count}
• ❌ Error: {error_count}

<b>รายละเอียด:</b>
"""
    
    for pair, signals in signals_by_pair.items():
        summary += f"\n• <b>{pair}:</b> " + " | ".join(signals)
    
    summary += f"\n\n<b>รอบถัดไป:</b> อีก 5 นาที"
    
    return summary


async def run_scanner():
    """Run Scanner Agent และส่งผลลัพธ์ไป Telegram"""
    timestamp = datetime.now().isoformat()
    log_path = Path(__file__).parent.parent / 'logs' / 'scanner_runs.jsonl'
    
    try:
        # Send startup notification
        await send_startup_notification()
        
        print(f"🔍 Scanner Agent Run - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ICT")
        print("=" * 60)
        
        # Run scanner
        scanner = Scanner()
        results = await scanner.scan_market()
        
        print("\n📊 SCAN RESULTS SUMMARY")
        print("=" * 60)
        
        # Count signals and send alerts
        buy_signals = []
        
        for pair, timeframes in results.items():
            print(f"\n{pair}:")
            for tf, data in timeframes.items():
                if "error" not in data:
                    signal = data.get("signal", "HOLD")
                    print(f"  {tf}: {signal}")
                    
                    # Collect BUY signals for alert
                    if signal == "BUY":
                        buy_signals.append({
                            'pair': pair,
                            'timeframe': tf,
                            'confidence': data.get('confidence', 0)
                        })
                else:
                    print(f"  {tf}: ERROR - {data['error']}")
        
        # Generate summary
        summary = await generate_scanner_summary(results)
        
        # Send summary to Telegram
        telegram_success = await send_message(summary)
        
        # Send individual BUY alerts
        for signal in buy_signals:
            await send_signal_alert(
                pair=signal['pair'],
                signal="BUY",
                confidence=signal['confidence'] * 100
            )
        
        # Log results
        log_entry = {
            'timestamp': timestamp,
            'job': 'scanner-job',
            'status': 'completed',
            'results_summary': {
                'pairs_scanned': len(results),
                'buy_signals': len(buy_signals)
            }
        }
        
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        print("\n" + "=" * 60)
        print(f"Scan completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ICT")
        print(f"📱 Telegram: {'✅ Sent' if telegram_success else '❌ Failed'}")
        
        return True
        
    except Exception as e:
        # Log error
        error_entry = {
            'timestamp': timestamp,
            'job': 'scanner-job',
            'status': 'error',
            'error': str(e)
        }
        
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(error_entry, ensure_ascii=False) + '\n')
        
        # Send error alert
        await send_error_alert("Scanner Agent Error", str(e))
        
        print(f"Scanner Agent error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    success = asyncio.run(run_scanner())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
