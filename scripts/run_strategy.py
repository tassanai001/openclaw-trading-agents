#!/usr/bin/env python3
"""
Strategy Agent Runner

Combines scanner and sentiment signals to make trading decisions.
- Sends short Thai summary to Telegram (Direct Bot API)
- Saves full report to Markdown file
"""

import json
import sqlite3
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.strategy.strategy import StrategyAgent
from agents.scanner.config import get_pairs, get_timeframes
from config.telegram_bot import send_strategy_summary, send_error_alert, send_startup_notification


def get_db_connection():
    """Get database connection"""
    # Scanner uses data/state.db, sentiment uses trading.db
    return sqlite3.connect('data/state.db')


def get_sentiment_db_connection():
    """Get sentiment database connection"""
    return sqlite3.connect('trading.db')


def get_latest_sentiment(symbol: str = None) -> float:
    """Get latest sentiment score from cache"""
    conn = get_sentiment_db_connection()
    cursor = conn.cursor()
    
    if symbol:
        cursor.execute('''
            SELECT sentiment_score FROM sentiment_cache 
            WHERE symbol = ? 
            ORDER BY timestamp DESC LIMIT 1
        ''', (symbol,))
    else:
        # Get overall sentiment
        cursor.execute('''
            SELECT sentiment_score FROM sentiment_cache 
            WHERE symbol = 'OVERALL'
            ORDER BY timestamp DESC LIMIT 1
        ''')
    
    row = cursor.fetchone()
    conn.close()
    
    return row[0] if row else 0.0


def get_scanner_signals() -> dict:
    """
    Get latest scanner signals from cache.
    Returns dict of {pair: signal} - latest signal per pair
    Note: Scanner stores one signal per scan (not per timeframe in this table)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get latest signal for each pair from scan_cache
    cursor.execute('''
        SELECT pair, signal FROM scan_cache sc1
        WHERE timestamp = (
            SELECT MAX(timestamp) FROM scan_cache sc2 WHERE sc2.pair = sc1.pair
        )
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    signals = {}
    for row in rows:
        pair = row[0]
        signal = row[1]
        signals[pair] = signal
    
    return signals


def signal_to_numeric(signal: str) -> float:
    """Convert scanner signal to numeric value"""
    if signal == 'BUY':
        return 0.5
    elif signal == 'SELL':
        return -0.5
    else:  # HOLD or unknown
        return 0.0


def generate_thai_summary(decisions: list, sentiment_score: float) -> str:
    """
    Generate short Thai summary for Telegram (under 4000 chars)
    """
    timestamp = datetime.now().strftime('%H:%M')
    
    long_count = sum(1 for d in decisions if d['decision']['decision'] == 'LONG')
    short_count = sum(1 for d in decisions if d['decision']['decision'] == 'SHORT')
    wait_count = sum(1 for d in decisions if d['decision']['decision'] == 'WAIT')
    
    # Sentiment interpretation
    if sentiment_score > 0.3:
        sentiment_text = "บวกแข็ง 💪"
    elif sentiment_score > 0.1:
        sentiment_text = "บวกเล็กน้อย 📈"
    elif sentiment_score > -0.1:
        sentiment_text = "กลางๆ ➡️"
    elif sentiment_score > -0.3:
        sentiment_text = "ลบเล็กน้อย 📉"
    else:
        sentiment_text = "ลบแข็ง 💔"
    
    # Build summary
    summary = f"""🤖 สรุป Strategy Agent ({timestamp})

สถานะ: ✅ สำเร็จ

สัญญาณ:
• LONG: {long_count}
• SHORT: {short_count}
• WAIT: {wait_count}

Sentiment: {sentiment_score:.3f} ({sentiment_text})

รอบถัดไป: อีก 5 นาที

📄 รายงานเต็ม: research-reports/strategy-{datetime.now().strftime('%Y-%m-%d-%H%M')}.md"""
    
    return summary


def save_full_report(decisions: list, sentiment_score: float, report_path: Path):
    """
    Save full detailed report to Markdown file
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    long_count = sum(1 for d in decisions if d['decision']['decision'] == 'LONG')
    short_count = sum(1 for d in decisions if d['decision']['decision'] == 'SHORT')
    wait_count = sum(1 for d in decisions if d['decision']['decision'] == 'WAIT')
    
    # Sentiment interpretation
    if sentiment_score > 0.3:
        sentiment_text = "บวกแข็ง (Bullish)"
    elif sentiment_score > 0.1:
        sentiment_text = "บวกเล็กน้อย (Slightly Bullish)"
    elif sentiment_score > -0.1:
        sentiment_text = "กลางๆ (Neutral)"
    elif sentiment_score > -0.3:
        sentiment_text = "ลบเล็กน้อย (Slightly Bearish)"
    else:
        sentiment_text = "ลบแข็ง (Bearish)"
    
    report = f"""# 🤖 Strategy Agent Report

**วันที่:** {timestamp}  
**สถานะ:** ✅ สำเร็จ

---

## 📊 สรุปผลการวิเคราะห์

| เมตริก | ค่า |
|--------|-----|
| Sentiment Score | {sentiment_score:.3f} |
| Sentiment | {sentiment_text} |
| สัญญาณ LONG | {long_count} |
| สัญญาณ SHORT | {short_count} |
| สัญญาณ WAIT | {wait_count} |
| รวมทั้งหมด | {len(decisions)} pairs |

---

## 📈 รายละเอียดสัญญาณแต่ละ Pair

| Pair | Scanner Signal | Decision | Combined Signal | Position Size |
|------|----------------|----------|-----------------|---------------|
"""
    
    for d in decisions:
        pair = d['pair']
        scanner = d['scanner_signal']
        decision = d['decision']['decision']
        combined = d['decision']['combined_signal']
        position_size = d['decision']['position_size']
        
        report += f"| {pair} | {scanner} | {decision} | {combined:.3f} | {position_size:.2%} |\n"
    
    report += f"""
---

## 🧠 การวิเคราะห์

### Sentiment Analysis
- **Score:** {sentiment_score:.3f}
- **Interpretation:** {sentiment_text}
- **Impact:** Sentiment มีน้ำหนัก 40% ในการตัดสินใจ

### Strategy Logic
- **Scanner Weight:** 60%
- **Sentiment Weight:** 40%
- **Position Sizing:** 2% ต่อ trade (สูงสุด 5%)

### Risk Parameters
- **Max Position Size:** 2% ของพอร์ต
- **Daily Loss Limit:** 5%
- **Max Open Positions:** 5

---

## 📝 หมายเหตุ

- รายงานนี้สร้างอัตโนมัติโดย Strategy Agent
- ข้อมูลมาจาก scan_cache และ sentiment_cache
- การตัดสินใจเป็นเพียงคำแนะนำ ต้องผ่าน Risk Agent ก่อน execute

---

*สร้างโดย OpenClaw Trading Agents*
"""
    
    # Save report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return str(report_path)


async def run_strategy_agent_async():
    """Run the strategy agent and log results (async version)"""
    timestamp = datetime.now().isoformat()
    log_path = Path(__file__).parent.parent / 'logs' / 'strategy_runs.jsonl'
    report_path = Path(__file__).parent.parent / 'research-reports' / f'strategy-{datetime.now().strftime("%Y-%m-%d-%H%M")}.md'
    
    try:
        # Initialize strategy agent
        strategy = StrategyAgent()
        
        # Get scanner signals
        scanner_signals = get_scanner_signals()
        
        # Get sentiment score
        sentiment_score = get_latest_sentiment()
        
        decisions = []
        
        # Process each pair (scanner provides one signal per pair)
        pairs = get_pairs()
        
        for pair in pairs:
            # Get scanner signal for this pair
            scanner_signal_str = scanner_signals.get(pair, 'HOLD')
            scanner_signal_num = signal_to_numeric(scanner_signal_str)
            
            # Make strategy decision
            decision = strategy.make_decision(scanner_signal_num, sentiment_score)
            
            decisions.append({
                'pair': pair,
                'scanner_signal': scanner_signal_str,
                'sentiment_score': sentiment_score,
                'decision': decision
            })
        
        # Generate Thai summary for Telegram (short)
        thai_summary = generate_thai_summary(decisions, sentiment_score)
        
        # Save full report to Markdown (detailed)
        report_file = save_full_report(decisions, sentiment_score, report_path)
        
        # Prepare log entry
        log_entry = {
            'timestamp': timestamp,
            'job': 'strategy-job',
            'status': 'completed',
            'decisions': decisions,
            'summary': f"Processed {len(decisions)} pairs. Sentiment: {sentiment_score:.3f}",
            'telegram_message': thai_summary,
            'report_file': str(report_file)
        }
        
        # Write to log file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        # Send to Telegram via Direct Bot API
        telegram_success = await send_strategy_summary(thai_summary)
        
        # Print summary (for console logging)
        print(thai_summary)
        print(f"\n📄 Full report saved: {report_file}")
        print(f"📱 Telegram: {'✅ Sent' if telegram_success else '❌ Failed'}")
        
        return True
        
    except Exception as e:
        # Log error
        error_entry = {
            'timestamp': timestamp,
            'job': 'strategy-job',
            'status': 'error',
            'error': str(e)
        }
        
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(error_entry, ensure_ascii=False) + '\n')
        
        # Send error alert to Telegram
        await send_error_alert("Strategy Agent Error", str(e))
        
        print(f"Strategy Agent error: {e}")
        return False


def run_strategy_agent():
    """Run the strategy agent (sync wrapper)"""
    return asyncio.run(run_strategy_agent_async())


if __name__ == '__main__':
    # Send startup notification
    asyncio.run(send_startup_notification())
    
    # Run strategy agent
    success = run_strategy_agent()
    sys.exit(0 if success else 1)
