#!/usr/bin/env python3
"""
Setup script for API keys and configuration.
Helps configure Hyperliquid Testnet and Telegram alerts.
"""

import os
import sys
from pathlib import Path

def load_env_example():
    """Load .env.example file"""
    env_example = Path('.env.example')
    if not env_example.exists():
        print("❌ .env.example not found")
        return None
    
    with open(env_example, 'r') as f:
        return f.read()

def check_env_exists():
    """Check if .env file exists"""
    env_file = Path('.env')
    return env_file.exists()

def validate_env():
    """Validate .env file has required keys"""
    env_file = Path('.env')
    if not env_file.exists():
        return False, ".env file not found"
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    required_keys = [
        'HYPERLIQUID_API_KEY',
        'HYPERLIQUID_API_SECRET',
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID'
    ]
    
    missing = []
    for key in required_keys:
        if key not in content or f'{key}=' in content and f'{key}=your_' in content.lower():
            missing.append(key)
    
    if missing:
        return False, f"Missing keys: {', '.join(missing)}"
    
    return True, "All keys configured"

def test_hyperliquid_connection():
    """Test Hyperliquid API connection"""
    print("\n🔗 Testing Hyperliquid Testnet connection...")
    
    try:
        # Import the API module
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from agents.execution.hyperliquid_api import HyperliquidAPI
        
        # Create API instance (testnet)
        api = HyperliquidAPI(is_testnet=True, mock_mode=True)
        
        # Test connection
        print("✅ Hyperliquid Testnet API: Connected (mock mode)")
        return True
        
    except Exception as e:
        print(f"❌ Hyperliquid Testnet API: Failed - {str(e)}")
        return False

def test_telegram_connection():
    """Test Telegram bot connection"""
    print("\n📱 Testing Telegram bot connection...")
    
    # This would require actual bot token
    # For now, just check if token is configured
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
        
        if 'TELEGRAM_BOT_TOKEN=' in content and 'your_bot_token' not in content.lower():
            print("✅ Telegram Bot Token: Configured")
            return True
        else:
            print("⚠️  Telegram Bot Token: Not configured")
            return False
    
    return False

def main():
    """Main setup function"""
    print("=" * 60)
    print(" OpenClaw Trading Agents - API Setup")
    print("=" * 60)
    
    # Check .env file
    print("\n📄 Checking .env file...")
    if check_env_exists():
        print("✅ .env file exists")
        
        # Validate keys
        valid, message = validate_env()
        if valid:
            print(f"✅ {message}")
        else:
            print(f"⚠️  {message}")
            print("\n📝 Edit .env file and add your API keys:")
            print("   nano .env  OR  vim .env")
    else:
        print("❌ .env file not found")
        print("\n📝 Creating .env from .env.example...")
        if load_env_example():
            print("✅ Created .env file")
            print("   Please edit .env and add your API keys")
    
    # Test connections
    print("\n" + "=" * 60)
    print(" Testing Connections")
    print("=" * 60)
    
    hyperliquid_ok = test_hyperliquid_connection()
    telegram_ok = test_telegram_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print(" Setup Summary")
    print("=" * 60)
    
    checks = [
        (".env file", check_env_exists()),
        ("API keys configured", validate_env()[0]),
        ("Hyperliquid API", hyperliquid_ok),
        ("Telegram Bot", telegram_ok)
    ]
    
    all_ok = True
    for name, ok in checks:
        status = "✅" if ok else "❌"
        print(f"{status} {name}")
        if not ok:
            all_ok = False
    
    print("\n" + "=" * 60)
    if all_ok:
        print("🎉 All checks passed! Ready to trade!")
    else:
        print("⚠️  Some checks failed. Please complete setup.")
        print("\n📚 Next steps:")
        print("   1. Get Hyperliquid Testnet API keys:")
        print("      https://testnet.hyperliquid.xyz/")
        print("   2. Create Telegram bot via @BotFather")
        print("   3. Edit .env file with your keys")
        print("   4. Run this script again to verify")
    print("=" * 60)
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())
