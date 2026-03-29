#!/usr/bin/env python3
"""
Verify that sentiment analysis is working with real data sources and mock disabled.
"""

import asyncio
import os
import sys
import pathlib

# Add project root to Python path if running as standalone script
script_dir = pathlib.Path(__file__).parent.resolve()
project_root = script_dir.parent if script_dir.name == 'tests' else script_dir
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sentiment.sentiment import SentimentAgent
from agents.sentiment.config import SentimentConfig

async def main():
    print("🔍 Verifying Sentiment Analysis Setup")
    print("=" * 50)
    
    # Check environment variables
    twitter_token = os.getenv('TWITTER_BEARER_TOKEN')
    cryptopanic_key = os.getenv('CRYPTOPANIC_API_KEY')
    
    print(f"Twitter Bearer Token: {'✅ SET' if twitter_token else '❌ NOT SET'}")
    print(f"CryptoPanic API Key: {'✅ SET' if cryptopanic_key else '⚠️  OPTIONAL'}")
    
    # Create sentiment agent with real mode enabled
    config = SentimentConfig(
        use_real_sentiment=True,
        twitter_bearer_token=twitter_token,
        cryptopanic_api_key=cryptopanic_key
    )
    
    agent = SentimentAgent(config)
    
    print(f"\nSentiment Agent Configuration:")
    print(f"  - Use Real Sentiment: {agent.use_real_sentiment}")
    print(f"  - Twitter Enabled: {agent.twitter_client.enabled}")
    print(f"  - News Enabled: {agent.news_client.enabled}")
    
    # Test with sample data
    print(f"\n🧪 Testing Sentiment Analysis...")
    
    sample_tweets = ["Bitcoin showing strong bullish momentum! 🚀"]
    sample_news = [{"title": "Crypto Market Rebounds", "content": "Positive outlook for Bitcoin"}]
    
    try:
        result = await agent.get_overall_sentiment(
            twitter_data=sample_tweets,
            news_data=sample_news,
            include_fng=True,
            trading_pairs=["BTC/USDT"]
        )
        
        combined_score = result['combined']['sentiment_score']
        sources_used = result['combined']['sources_used']
        
        print(f"\n✅ Sentiment Analysis Successful!")
        print(f"   Combined Score: {combined_score:.3f}")
        print(f"   Sources Used: {', '.join(sources_used)}")
        
        # Verify mock is not being used
        if 'mock_generator' in sources_used:
            print(f"\n❌ ISSUE: Mock data is still being used!")
            print(f"   This means real data sources are not available.")
            if not twitter_token:
                print(f"   ➡️  Set TWITTER_BEARER_TOKEN to enable Twitter sentiment")
            if not cryptopanic_key:
                print(f"   ➡️  Set CRYPTOPANIC_API_KEY to enable News sentiment")
        else:
            print(f"\n✅ SUCCESS: Mock data is DISABLED!")
            print(f"   System is using real data sources only.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)