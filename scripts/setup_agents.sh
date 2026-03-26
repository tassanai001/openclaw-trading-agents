#!/bin/bash
# setup_agents.sh - Initialize trading agents

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " OpenClaw Trading Agents - Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create directories
echo "📁 Creating directory structure..."
mkdir -p agents/{scanner,sentiment,strategy,risk,execution,learning}
mkdir -p data
mkdir -p memory/{daily_reports,performance}
mkdir -p config
mkdir -p scripts
mkdir -p logs
mkdir -p tests
mkdir -p documents

# Initialize database
echo "🗄️  Initializing SQLite database..."
python3 -c "
import sqlite3
from config.db_schema import DB_SCHEMA
conn = sqlite3.connect('data/state.db')
conn.executescript(DB_SCHEMA)
conn.commit()
conn.close()
print('✅ Database initialized: data/state.db')
"

# Create .env example
echo "📝 Creating environment template..."
cat > .env.example << 'EOF'
# Hyperliquid API (Testnet)
HYPERLIQUID_API_KEY=your_testnet_api_key
HYPERLIQUID_API_SECRET=your_testnet_api_secret

# Telegram Alerts
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# OpenAI (for vision analysis - optional)
OPENAI_API_KEY=your_openai_api_key

# Trading Mode
TRADING_MODE=testnet  # testnet or production
DRY_RUN=true  # true for paper trading
EOF

echo "✅ Environment template created: .env.example"

# Verify structure
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Setup Complete! ✓"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and fill in your API keys"
echo "2. Install dependencies: pip install -r requirements.txt"
echo "3. Run tests: pytest tests/"
echo ""
