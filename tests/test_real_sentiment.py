#!/usr/bin/env python3
"""
Test real sentiment analysis with mock data disabled.
This test uses keyword-based analysis (no PyTorch required) but disables mock fallback.
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

async def test_real_sentiment_without_mock():
    """Test sentiment analysis with real data sources and mock disabled"""
    
    # Create config with real sentiment enabled (mock disabled)
    config = SentimentConfig(
        use_real_sentiment=True,
        twitter_bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
        cryptopanic_api_key=os.getenv('CRYPTOPANIC_API_KEY')
    )
    
    agent = SentimentAgent(config)
    
    print("Testing real sentiment analysis (mock disabled)...")
    print(f"Use real sentiment: {agent.use_real_sentiment}")
    print(f"Twitter enabled: {agent.twitter_client.enabled}")
    print(f"News enabled: {agent.news_client.enabled}")
    
    # Test with sample data (simulating real data)
    sample_tweets = [
        "Bitcoin is showing strong bullish momentum! 🚀",
        "Market sentiment turning positive for crypto",
        "Great gains expected in the coming weeks"
    ]
    
    sample_news = [
        {"title": "Crypto Market Rebounds", "content": "Bitcoin shows strong recovery with positive outlook"},
        {"title": "Institutional Interest Grows", "content": "Major institutions increasing crypto holdings"}
    ]
    
    # Get overall sentiment
    result = await agent.get_overall_sentiment(
        twitter_data=sample_tweets,
        news_data=sample_news,
        include_fng=True,
        trading_pairs=["BTC/USDT", "ETH/USDT"]
    )
    
    print("\nSentiment Analysis Results:")
    print(f"Combined score: {result['combined']['sentiment_score']}")
    print(f"Sources used: {result['combined']['sources_used']}")
    
    # Verify mock was not used
    if 'mock_generator' in result['combined']['sources_used']:
        print("❌ ERROR: Mock data was used (should be disabled)")
        return False
    else:
        print("✅ SUCCESS: Mock data disabled, using real analysis")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_real_sentiment_without_mock())
    exit(0 if success else 1)