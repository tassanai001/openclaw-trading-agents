#!/bin/bash
# health_check.sh - System health check

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " OpenClaw Trading Agents - Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Python version
echo "🐍 Python Version:"
python3 --version

# Check database
echo ""
echo "🗄️  Database Status:"
if [ -f "data/state.db" ]; then
    echo "✅ Database exists: data/state.db"
    TABLES=$(sqlite3 data/state.db ".tables")
    echo "   Tables: $TABLES"
else
    echo "❌ Database not found!"
    exit 1
fi

# Check directories
echo ""
echo "📁 Directory Structure:"
for dir in agents/scanner agents/sentiment agents/strategy agents/risk agents/execution agents/learning memory/daily_reports memory/performance logs tests; do
    if [ -d "$dir" ]; then
        echo "✅ $dir"
    else
        echo "❌ $dir (missing)"
    fi
done

# Check config files
echo ""
echo "⚙️  Configuration Files:"
for file in config/trading_config.py config/agents_config.yaml config/db_schema.py; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "⚠️  $file (missing)"
    fi
done

# Check environment
echo ""
echo "🔐 Environment:"
if [ -f ".env" ]; then
    echo "✅ .env exists"
    # Check for required vars (without exposing values)
    if grep -q "HYPERLIQUID_API_KEY=" .env && [ "$(grep "HYPERLIQUID_API_KEY=" .env | cut -d'=' -f2)" != "your_testnet_api_key" ]; then
        echo "✅ Hyperliquid API key configured"
    else
        echo "⚠️  Hyperliquid API key not set"
    fi
else
    echo "⚠️  .env not found (copy from .env.example)"
fi

# Check dependencies
echo ""
echo "📦 Python Dependencies:"
python3 -c "import pandas; print('✅ pandas')" 2>/dev/null || echo "❌ pandas (missing)"
python3 -c "import pandas_ta; print('✅ pandas-ta')" 2>/dev/null || echo "❌ pandas-ta (missing)"
python3 -c "import yaml; print('✅ pyyaml')" 2>/dev/null || echo "❌ pyyaml (missing)"
python3 -c "import dotenv; print('✅ python-dotenv')" 2>/dev/null || echo "❌ python-dotenv (missing)"

# Database integrity check
echo ""
echo "🔍 Database Integrity:"
INTEGRITY=$(sqlite3 data/state.db "PRAGMA integrity_check;")
if [ "$INTEGRITY" = "ok" ]; then
    echo "✅ Database integrity: OK"
else
    echo "❌ Database integrity: FAILED"
    exit 1
fi

# Count records
echo ""
echo "📊 Database Statistics:"
echo "   Portfolio states: $(sqlite3 data/state.db "SELECT COUNT(*) FROM portfolio_state;")"
echo "   Open positions: $(sqlite3 data/state.db "SELECT COUNT(*) FROM positions WHERE status='OPEN';")"
echo "   Total trades: $(sqlite3 data/state.db "SELECT COUNT(*) FROM trade_log;")"
echo "   Performance records: $(sqlite3 data/state.db "SELECT COUNT(*) FROM performance_metrics;")"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Health Check Complete ✓"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
