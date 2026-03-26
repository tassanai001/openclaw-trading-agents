#!/usr/bin/env python3
"""
Sentiment Agent Runner with Direct Telegram API
- วิเคราะห์ sentiment และส่งสรุปผ่าน Telegram โดยตรง
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

from agents.sentiment.sentiment import SentimentAgent
from config.telegram_bot import (
    send_startup_notification,
    send_message,
    send_error_alert
)


async def fetch_crypto_fear_greed():
    """Fetch Crypto Fear & Greed Index"""
    try:
        import urllib.request
        url = "https://api.alternative.me/fng/"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data['data'][0]
    except Exception as e:
        return {'error': str(e)}


def get_fng_label(score):
    """Convert Fear & Greed score to label"""
    if score <= 24:
        return "Extreme Fear 🔴"
    elif score <= 45:
        return "Fear 🟡"
    elif score <= 55:
        return "Neutral ⚪"
    elif score <= 75:
        return "Greed 🟢"
    else:
        return "Extreme Greed 🟢"


def get_sentiment_emoji(score: float) -> str:
    """Convert sentiment score to emoji"""
    if score > 0.3:
        return "🟢"
    elif score > 0.1:
        return "📈"
    elif score > -0.1:
        return "➡️"
    elif score > -0.3:
        return "📉"
    else:
        return "🔴"


async def generate_sentiment_summary(fng_data: dict, combined_sentiment: float) -> str:
    """สร้างสรุป Sentiment สำหรับ Telegram"""
    timestamp = datetime.now().strftime('%H:%M')
    
    # F&G data
    fng_value = int(fng_data.get('value', 50)) if 'error' not in fng_data else None
    if fng_value:
        fng_label = get_fng_label(fng_value)
    else:
        fng_label = "N/A"
    
    # Sentiment interpretation
    if combined_sentiment > 0.3:
        sentiment_text = "บวกแข็ง (Bullish)"
    elif combined_sentiment > 0.1:
        sentiment_text = "บวกเล็กน้อย (Slightly Bullish)"
    elif combined_sentiment > -0.1:
        sentiment_text = "กลางๆ (Neutral)"
    elif combined_sentiment > -0.3:
        sentiment_text = "ลบเล็กน้อย (Slightly Bearish)"
    else:
        sentiment_text = "ลบแข็ง (Bearish)"
    
    emoji = get_sentiment_emoji(combined_sentiment)
    
    summary = f"""🐦 <b>Sentiment Agent Summary</b> ({timestamp})

<b>สถานะ:</b> ✅ สำเร็จ

<b>Fear & Greed Index:</b>
• Score: {fng_value}/100 ({fng_label})

<b>Combined Sentiment:</b>
• Score: {combined_sentiment:.3f}
• Signal: {sentiment_text} {emoji}

<b>รอบถัดไป:</b> อีก 5 นาที
"""
    
    return summary


async def run_sentiment():
    """Run Sentiment Agent และส่งผลลัพธ์ไป Telegram"""
    timestamp = datetime.now().isoformat()
    log_path = Path(__file__).parent.parent / 'logs' / 'sentiment_runs.jsonl'
    
    try:
        # Send startup notification
        await send_startup_notification()
        
        print(f"🐦 Sentiment Agent Run - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ICT")
        print("=" * 60)
        
        # Initialize agent
        sentiment_agent = SentimentAgent()
        
        # Fetch Fear & Greed
        fng_data = await fetch_crypto_fear_greed()
        
        if 'error' not in fng_data:
            fng_value = int(fng_data.get('value', 50))
            fng_previous = int(fng_data.get('previous_value', 50))
            fng_change = fng_value - fng_previous
            
            print(f"\n📊 Fear & Greed Index:")
            print(f"  Current: {fng_value}/100 ({get_fng_label(fng_value)})")
            print(f"  Previous: {fng_previous}/100")
            print(f"  Change: {fng_change:+d}")
            
            # Calculate F&G sentiment score (-1 to 1)
            fng_score = (fng_value / 50) - 1
        else:
            print(f"\n⚠️  Could not fetch F&G: {fng_data['error']}")
            fng_score = 0.0
        
        # Mock stock sentiment (in production, fetch real data)
        stock_sentiment = 0.0  # Neutral
        
        # Combined sentiment
        combined_sentiment = (fng_score + stock_sentiment) / 2
        
        print(f"\n📈 Combined Sentiment: {combined_sentiment:.3f}")
        
        # Generate summary
        summary = await generate_sentiment_summary(fng_data, combined_sentiment)
        
        # Send to Telegram
        telegram_success = await send_message(summary)
        
        # Save report
        report_dir = Path(__file__).parent.parent / 'reports'
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_filename = report_dir / f"sentiment_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.md"
        
        fng_label_display = get_fng_label(fng_value) if fng_value else "N/A"
        
        report = f"""# Market Sentiment Analysis Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ICT

---

## Summary

| Metric | Value |
|--------|-------|
| Fear & Greed | {fng_value}/100 ({fng_label_display}) if fng_value else "N/A" |
| Combined Sentiment | {combined_sentiment:.3f} |
| Signal | {get_sentiment_emoji(combined_sentiment)} |

---

*Generated by Sentiment Agent*
"""
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Log results
        log_entry = {
            'timestamp': timestamp,
            'job': 'sentiment-job',
            'status': 'completed',
            'sentiment_score': combined_sentiment,
            'fng_value': fng_value if 'error' not in fng_data else None
        }
        
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        print("\n" + "=" * 60)
        print(f"Sentiment analysis completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ICT")
        print(f"📱 Telegram: {'✅ Sent' if telegram_success else '❌ Failed'}")
        print(f"📄 Report saved: {report_filename}")
        
        return True
        
    except Exception as e:
        # Log error
        error_entry = {
            'timestamp': timestamp,
            'job': 'sentiment-job',
            'status': 'error',
            'error': str(e)
        }
        
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(error_entry, ensure_ascii=False) + '\n')
        
        # Send error alert
        await send_error_alert("Sentiment Agent Error", str(e))
        
        print(f"Sentiment Agent error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    success = asyncio.run(run_sentiment())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
