#!/usr/bin/env python3
"""
Bot Health Check Script
Checks bot status, positions, and alerts on issues
"""
import asyncio
import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_bot_health():
    """Check bot health and return status"""
    issues = []
    warnings = []
    status = {"ok": True, "timestamp": datetime.now().isoformat()}
    
    # Check database
    try:
        conn = sqlite3.connect('trading.db')
        cursor = conn.cursor()
        
        # Check trades count
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        status["total_trades"] = trade_count
        
        # Check recent trades (last 30 min)
        cursor.execute("""
            SELECT COUNT(*) FROM trades 
            WHERE timestamp > datetime('now', '-30 minutes')
        """)
        recent_trades = cursor.fetchone()[0]
        status["recent_trades"] = recent_trades
        
        # Check portfolio state
        cursor.execute("SELECT * FROM portfolio_state ORDER BY timestamp DESC LIMIT 1")
        portfolio = cursor.fetchone()
        if portfolio:
            status["portfolio"] = {
                "balance": portfolio[2],
                "pnl": portfolio[4]
            }
        
        # Check positions
        cursor.execute("SELECT COUNT(*) FROM positions")
        position_count = cursor.fetchone()[0]
        status["open_positions"] = position_count
        
        conn.close()
        
    except Exception as e:
        issues.append(f"Database error: {e}")
        status["ok"] = False
    
    # Check log files
    log_dir = Path('logs')
    if log_dir.exists():
        # Check for recent errors (last 1 hour only)
        from datetime import timedelta
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        for log_file in log_dir.glob('*.log'):
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-100:]  # Last 100 lines
                    # Count only recent errors (exclude aiohttp unclosed session warnings)
                    recent_errors = []
                    for l in lines:
                        # Skip non-critical aiohttp cleanup warnings
                        if 'Unclosed client session' in l or 'Unclosed connector' in l:
                            continue
                        if 'ERROR' in l or 'Exception' in l or 'Traceback' in l:
                            # Try to parse timestamp
                            try:
                                ts_str = l.split(' - ')[0]
                                ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S,%f')
                                if ts > one_hour_ago:
                                    recent_errors.append(l)
                            except:
                                recent_errors.append(l)  # Count if can't parse
                    
                    if recent_errors:
                        warnings.append(f"{log_file.name}: {len(recent_errors)} recent errors")
            except:
                pass
    
    # Check if bot completed recent cycles successfully
    try:
        cycle_log = Path('logs/trading_cycle.log')
        if cycle_log.exists():
            with open(cycle_log, 'r') as f:
                lines = f.readlines()[-20:]
                # Check if last cycle completed successfully
                for l in reversed(lines):
                    if 'completed successfully' in l:
                        status["bot_running"] = True
                        break
                    elif 'ERROR' in l or 'Exception' in l or 'Traceback' in l:
                        if 'Unclosed' not in l:  # Skip aiohttp warnings
                            status["bot_running"] = False
                            break
                else:
                    status["bot_running"] = "unknown"
        else:
            status["bot_running"] = False
    except:
        status["bot_running"] = "unknown"
    
    # Determine overall status
    if issues:
        status["status"] = "ERROR"
        status["issues"] = issues
    elif warnings:
        status["status"] = "WARNING"
        status["warnings"] = warnings
    else:
        status["status"] = "OK"
    
    return status

def escape_markdown_v2(text):
    """Escape special characters for MarkdownV2 parse mode"""
    # Characters that need escaping in MarkdownV2
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def send_telegram_alert(message):
    """Send alert via Telegram"""
    try:
        import subprocess
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not token or not chat_id:
            print("❌ Telegram Bot Token or Chat ID not configured")
            return False
        
        # Escape special characters for MarkdownV2
        escaped_message = escape_markdown_v2(message)
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        subprocess.run([
            'curl', '-s', '-X', 'POST', url,
            '-d', f'chat_id={chat_id}',
            '-d', f'text={escaped_message}',
            '-d', 'parse_mode=MarkdownV2'
        ], check=False)
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")

def main():
    """Main health check function"""
    print(f"[{datetime.now().isoformat()}] Running health check...")
    
    status = check_bot_health()
    
    # Print status
    print(f"Status: {status['status']}")
    print(f"Total Trades: {status.get('total_trades', 'N/A')}")
    print(f"Recent Trades (30m): {status.get('recent_trades', 'N/A')}")
    print(f"Open Positions: {status.get('open_positions', 'N/A')}")
    print(f"Bot Running: {status.get('bot_running', 'N/A')}")
    
    if status.get('issues'):
        print(f"Issues: {status['issues']}")
    
    if status.get('warnings'):
        print(f"Warnings: {status['warnings']}")
    
    # Send alert if there are issues
    if status['status'] in ['ERROR', 'WARNING']:
        message = f"🚨 Bot Alert\n\n"
        message += f"Status: {status['status']}\n"
        message += f"Time: {status['timestamp']}\n\n"
        
        if status.get('issues'):
            message += "❌ Issues:\n"
            for issue in status['issues']:
                message += f"- {issue}\n"
        
        if status.get('warnings'):
            message += "⚠️ Warnings:\n"
            for warning in status['warnings']:
                message += f"- {warning}\n"
        
        message += f"\nTotal Trades: {status.get('total_trades', 'N/A')}"
        message += f"\nOpen Positions: {status.get('open_positions', 'N/A')}"
        
        send_telegram_alert(message)
        print(f"\n⚠️ Alert sent via Telegram")
    
    # Save status to file
    import json
    status_file = Path('logs/health_status.json')
    status_file.parent.mkdir(exist_ok=True)
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    print(f"\n✅ Health check complete. Status saved to {status_file}")
    
    return 0 if status['status'] == 'OK' else 1

if __name__ == '__main__':
    sys.exit(main())
