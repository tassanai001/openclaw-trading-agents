#!/bin/bash
# emergency_stop.sh - Emergency stop script for trading system

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " OpenClaw Trading Agents - EMERGENCY STOP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a emergency_stop.log
}

# Function to send alert notification
send_alert() {
    local message="$1"
    log "🚨 ALERT: $message"
    
    # Send desktop notification if available
    if command -v osascript >/dev/null 2>&1; then
        # macOS notification
        osascript -e "display notification \"$message\" with title \"OpenClaw Emergency Stop\" sound name \"Sosumi\""
    elif command -v notify-send >/dev/null 2>&1; then
        # Linux notification
        notify-send "OpenClaw Emergency Stop" "$message" --urgency=critical
    fi
    
    # Log to system log as well
    logger "OpenClaw Emergency Stop: $message"
}

# Function to stop all cron jobs
stop_cron_jobs() {
    log "Stopping all cron jobs..."
    
    # Get list of current cron jobs
    crontab -l 2>/dev/null > current_crontab
    
    if [ -s current_crontab ]; then
        # Remove all cron jobs
        echo "" | crontab -
        log "✅ All cron jobs stopped"
    else
        log "ℹ️  No cron jobs found to stop"
    fi
    
    # Clean up temporary file
    rm -f current_crontab
}

# Function to close all paper trading positions
close_paper_positions() {
    log "Closing all paper trading positions..."
    
    # Use Python to interact with the paper trading system
    # This assumes there's a way to close all positions through the execution agent
    python3 -c "
import sys
import os
sys.path.append('.')
from config.paper_trading_config import PaperTradingConfig
from agents.execution.execution import ExecutionAgent
from agents.execution.config import ExecutionConfig

try:
    # Initialize paper trading system
    paper_config = PaperTradingConfig(enabled=True)
    exec_config = ExecutionConfig(paper_trading=True)
    agent = ExecutionAgent(exec_config, paper_config)
    
    # Initialize the agent
    import asyncio
    asyncio.run(agent.initialize())
    
    # Get all open positions
    account_info = asyncio.run(agent.get_account_info())
    positions = account_info.get('positions', [])
    
    if positions:
        print(f'Found {len(positions)} open positions to close')
        for pos in positions:
            asset = pos['asset']
            size = pos['size']
            side = 'S' if size > 0 else 'B'  # Close long with sell, close short with buy
            close_size = abs(size)
            
            print(f'Closing position: {asset} {side} {close_size}')
            
            # Place order to close position
            result = asyncio.run(agent.place_order(
                asset=asset,
                side=side,
                leverage=pos.get('leverage', 1),
                order_type='market',
                price=None,  # Market order to close
                size=close_size
            ))
            
            if result.success:
                print(f'✅ Successfully closed {asset} position')
            else:
                print(f'⚠️ Failed to close {asset} position: {result.error}')
    else:
        print('No open positions found')
        
    print('Paper positions closure complete')
except Exception as e:
    print(f'Error closing paper positions: {str(e)}')
    import traceback
    traceback.print_exc()
"
    
    if [ $? -eq 0 ]; then
        log "✅ All paper trading positions closed"
    else
        log "⚠️ Error occurred while closing paper positions"
    fi
}

# Main emergency stop procedure
log "Emergency stop initiated!"

# Send initial alert
send_alert "EMERGENCY STOP INITIATED - Stopping all trading activities"

# Step 1: Stop all cron jobs
stop_cron_jobs

# Step 2: Close all paper trading positions
close_paper_positions

# Step 3: Additional safety measures
log "Performing additional safety measures..."

# Kill any running trading processes
log "Terminating any active trading processes..."
pkill -f "run_cycle.py" 2>/dev/null || true
pkill -f "orchestrator.py" 2>/dev/null || true
pkill -f "openclaw" 2>/dev/null || true

# Create emergency stop indicator file
touch EMERGENCY_STOP_ACTIVE
log "Emergency stop indicator file created"

# Final alert
final_message="EMERGENCY STOP COMPLETED - All trading activities suspended"
log "$final_message"
send_alert "$final_message"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Emergency Stop Complete ✓"
echo " All cron jobs stopped and positions closed"
echo " Trading system suspended for safety"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Exit with error code to indicate emergency stop
exit 1