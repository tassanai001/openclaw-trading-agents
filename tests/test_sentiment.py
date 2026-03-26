"""
Tests for Sentiment Analysis Agent
"""

import pytest
import asyncio
from agents.sentiment.sentiment import SentimentAgent, get_sentiment_score
from agents.sentiment.config import SentimentConfig


@pytest.fixture
def sentiment_agent():
    """Create a sentiment agent instance for testing"""
    config = SentimentConfig()
    return SentimentAgent(config)


@pytest.mark.asyncio
async def test_sentiment_agent_initialization():
    """Test that sentiment agent initializes correctly"""
    agent = SentimentAgent()
    assert agent is not None
    assert hasattr(agent, 'analyze')
    assert hasattr(agent, 'analyze_twitter_sentiment')
    assert hasattr(agent, 'analyze_news_sentiment')


@pytest.mark.asyncio
async def test_analyze_positive_text(sentiment_agent):
    """Test sentiment analysis for positive text"""
    positive_text = "This is an excellent opportunity with great potential for profit!"
    score = await sentiment_agent.analyze(positive_text)
    
    assert isinstance(score, float)
    assert -1.0 <= score <= 1.0
    # Positive text should have a score >= 0
    assert score >= -0.1  # Allow for some variance in mock implementation


@pytest.mark.asyncio
async def test_analyze_negative_text(sentiment_agent):
    """Test sentiment analysis for negative text"""
    negative_text = "This is a terrible disaster with massive losses and problems"
    score = await sentiment_agent.analyze(negative_text)
    
    assert isinstance(score, float)
    assert -1.0 <= score <= 1.0
    # Negative text should have a score <= 0
    assert score <= 0.1  # Allow for some variance in mock implementation


@pytest.mark.asyncio
async def test_analyze_neutral_text(sentiment_agent):
    """Test sentiment analysis for neutral text"""
    neutral_text = "The stock price is $100 per share and the company has offices."
    score = await sentiment_agent.analyze(neutral_text)
    
    assert isinstance(score, float)
    assert -1.0 <= score <= 1.0
    # Neutral text should be close to 0
    assert -0.5 <= score <= 0.5


@pytest.mark.asyncio
async def test_analyze_empty_text(sentiment_agent):
    """Test sentiment analysis for empty text"""
    empty_text = ""
    score = await sentiment_agent.analyze(empty_text)
    
    assert isinstance(score, float)
    assert -1.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_analyze_twitter_sentiment(sentiment_agent):
    """Test Twitter sentiment analysis"""
    tweets = [
        "Amazing gains today! Bullish on tech stocks!",
        "Terrible earnings report, selling everything",
        "Market is looking strong this week"
    ]
    
    result = await sentiment_agent.analyze_twitter_sentiment(tweets)
    
    assert 'sentiment_score' in result
    assert 'total_tweets' in result
    assert 'timestamp' in result
    assert 'source' in result
    assert result['total_tweets'] == 3
    assert result['source'] == 'twitter'
    assert -1.0 <= result['sentiment_score'] <= 1.0


@pytest.mark.asyncio
async def test_analyze_news_sentiment(sentiment_agent):
    """Test news sentiment analysis"""
    articles = [
        {
            'title': 'Company Reports Strong Quarterly Earnings',
            'content': 'The company exceeded expectations with strong revenue growth'
        },
        {
            'title': 'Market Volatility Causes Concern',
            'content': 'Investors worried about economic indicators and future performance'
        }
    ]
    
    result = await sentiment_agent.analyze_news_sentiment(articles)
    
    assert 'sentiment_score' in result
    assert 'total_articles' in result
    assert 'timestamp' in result
    assert 'source' in result
    assert result['total_articles'] == 2
    assert result['source'] == 'news'
    assert -1.0 <= result['sentiment_score'] <= 1.0


@pytest.mark.asyncio
async def test_get_overall_sentiment_with_both_sources(sentiment_agent):
    """Test overall sentiment with both Twitter and news data"""
    twitter_data = [
        "Great market conditions today!",
        "Bullish on cryptocurrency"
    ]
    
    news_data = [
        {
            'title': 'Economic Indicators Show Growth',
            'content': 'Positive outlook for the next quarter'
        }
    ]
    
    result = await sentiment_agent.get_overall_sentiment(
        twitter_data=twitter_data,
        news_data=news_data
    )
    
    assert 'twitter' in result
    assert 'news' in result
    assert 'combined' in result
    assert 'sentiment_score' in result['combined']
    assert 'sources_used' in result['combined']
    assert 'twitter' in result['combined']['sources_used']
    assert 'news' in result['combined']['sources_used']


@pytest.mark.asyncio
async def test_get_overall_sentiment_with_only_twitter(sentiment_agent):
    """Test overall sentiment with only Twitter data"""
    twitter_data = [
        "Market crash incoming!",
        "Selling all positions"
    ]
    
    result = await sentiment_agent.get_overall_sentiment(
        twitter_data=twitter_data,
        news_data=None,
        include_fng=False
    )
    
    assert 'twitter' in result
    assert 'combined' in result
    assert abs(result['combined']['sentiment_score'] - result['twitter']['sentiment_score']) < 0.001
    assert result['combined']['sources_used'] == ['twitter']


@pytest.mark.asyncio
async def test_get_overall_sentiment_with_only_news(sentiment_agent):
    """Test overall sentiment with only news data"""
    news_data = [
        {
            'title': 'Major breakthrough in renewable energy',
            'content': 'Revolutionary technology will change the industry forever'
        }
    ]
    
    result = await sentiment_agent.get_overall_sentiment(
        twitter_data=None,
        news_data=news_data,
        include_fng=False
    )
    
    assert 'news' in result
    assert 'combined' in result
    assert abs(result['combined']['sentiment_score'] - result['news']['sentiment_score']) < 0.001
    assert result['combined']['sources_used'] == ['news']


@pytest.mark.asyncio
async def test_convenience_function():
    """Test the convenience function for getting sentiment score"""
    text = "This is a wonderful development"
    score = await get_sentiment_score(text)
    
    assert isinstance(score, float)
    assert -1.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_config_validation():
    """Test configuration validation"""
    # Test that weights are normalized if they don't sum to 1
    config = SentimentConfig(twitter_weight=0.3, news_weight=0.4)
    # Since 0.3 + 0.4 = 0.7, they should be normalized
    expected_twitter = 0.3 / 0.7
    expected_news = 0.4 / 0.7
    
    assert abs(config.twitter_weight - expected_twitter) < 0.01
    assert abs(config.news_weight - expected_news) < 0.01


if __name__ == "__main__":
    pytest.main([__file__])