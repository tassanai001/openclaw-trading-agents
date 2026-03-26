#!/usr/bin/env python3
"""
register_crons.py - Register cron jobs for trading agents using OpenClaw system

Registers the following cron jobs:
1. Scanner cron (every 5 min)
2. Sentiment cron (every 5 min, parallel)
3. Strategy cron (every 5 min, after scanner+sentiment)
4. Monitoring cron (every hour)
"""

import subprocess
import json
import sys
import os
from pathlib import Path

def run_command(cmd, description="Running command"):
    """Execute a shell command and return the result."""
    print(f"🔧 {description}")
    print(f"   Command: {cmd}")
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"   ✓ Success: {result.stdout.strip() if result.stdout.strip() else 'Command completed'}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"   ✗ Error: {e.stderr.strip() if e.stderr.strip() else str(e)}")
        return False, e.stderr

def register_scanner_cron():
    """Register the Scanner cron job (every 5 minutes)."""
    cmd = "openclaw cron add --name scanner-job --cron '*/5 * * * *' --message 'Run Scanner Agent: analyze market data'"
    success, _ = run_command(cmd, "Registering Scanner cron (every 5 min)")
    return success

def register_sentiment_cron():
    """Register the Sentiment cron job (every 5 minutes, runs in parallel)."""
    cmd = "openclaw cron add --name sentiment-job --cron '*/5 * * * *' --message 'Run Sentiment Agent: analyze market sentiment'"
    success, _ = run_command(cmd, "Registering Sentiment cron (every 5 min, parallel)")
    return success

def register_strategy_cron():
    """Register the Strategy cron job (every 5 minutes, after scanner+sentiment)."""
    cmd = "openclaw cron add --name strategy-job --cron '*/5 * * * *' --message 'Run Strategy Agent: analyze signals from scanner and sentiment'"
    success, _ = run_command(cmd, "Registering Strategy cron (every 5 min, after scanner+sentiment)")
    return success

def register_monitoring_cron():
    """Register the Monitoring cron job (every hour)."""
    cmd = "openclaw cron add --name monitoring-job --cron '0 * * * *' --message 'Run Monitoring Agent: system health and performance'"
    success, _ = run_command(cmd, "Registering Monitoring cron (every hour)")
    return success

def load_cron_definitions(json_file):
    """Load cron job definitions from JSON file."""
    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  JSON file {json_file} not found. Using default definitions.")
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️  Error parsing JSON file {json_file}: {e}")
        return None

def register_cron_from_json(cron_def):
    """Register a single cron job from JSON definition."""
    name = cron_def.get('name', '')
    schedule = cron_def.get('schedule', '')
    message = cron_def.get('message', '')
    
    cmd = f"openclaw cron add --name {name} --cron '{schedule}' --message '{message}'"
    success, _ = run_command(cmd, f"Registering {name} cron ({schedule}): {message}")
    return success

def main():
    """Main function to register all cron jobs."""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(" OpenClaw Trading Agents - Register Cron Jobs (Python)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()
    
    # Check if openclaw command is available
    success, _ = run_command("which openclaw", "Checking if openclaw command is available")
    if not success:
        print("❌ Error: openclaw command not found. Please install OpenClaw system first.")
        sys.exit(1)
    
    print("\n📋 Cron Jobs to Register:")
    print()
    print("1. scanner-job (Every 5 minutes)")
    print("   Scanner agent analyzes market data")
    print()
    print("2. sentiment-job (Every 5 minutes, parallel)")
    print("   Sentiment agent analyzes market sentiment")
    print()
    print("3. strategy-job (Every 5 minutes, after scanner+sentiment)")
    print("   Strategy agent analyzes signals from scanner and sentiment")
    print()
    print("4. monitoring-job (Every hour)")
    print("   Monitoring agent checks system health and performance")
    print()
    
    # Try to load cron definitions from JSON
    json_file = Path(__file__).parent / "cron_jobs.json"
    cron_definitions = load_cron_definitions(json_file)
    
    successful_registrations = 0
    total_registrations = 4
    
    if cron_definitions and isinstance(cron_definitions, list):
        print(f"\n📝 Loading cron definitions from {json_file.name}")
        for cron_def in cron_definitions:
            if register_cron_from_json(cron_def):
                successful_registrations += 1
    else:
        print(f"\n📝 Registering default cron jobs...")
        
        # Register each cron job
        if register_scanner_cron():
            successful_registrations += 1
            
        if register_sentiment_cron():
            successful_registrations += 1
            
        if register_strategy_cron():
            successful_registrations += 1
            
        if register_monitoring_cron():
            successful_registrations += 1
    
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(" Registration Summary")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Successfully registered: {successful_registrations}/{total_registrations} cron jobs")
    
    if successful_registrations == total_registrations:
        print("✅ All cron jobs registered successfully!")
        return 0
    else:
        print(f"⚠️  Some cron jobs failed to register ({total_registrations - successful_registrations} failed)")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)