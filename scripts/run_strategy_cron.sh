#!/bin/bash
# Strategy Agent Cron Runner
# Runs the strategy agent and outputs short Thai summary for Telegram

cd /Users/nunamzza/projects/trading/openclaw-trading-agents

# Run the Python script
python3 scripts/run_strategy.py

# Exit with the same code as Python script
exit $?
