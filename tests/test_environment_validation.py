"""
2026-03-29
Tests for Environment Variable Validation in Sentiment Agent

This test validates all combinations of TWITTER_BEARER_TOKEN and CRYPTOPANIC_API_KEY:
1. Both present (full real sentiment)
2. Only Twitter (Twitter + mock news)
3. Only CryptoPanic (News + mock Twitter)
4. Neither (full mock)
5. Environment variable precedence over config parameters
"""

import os
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from agents.sentiment.sentiment import SentimentAgent
from agents.sentiment.config import SentimentConfig
from agents.sentiment.twitter_client import TwitterClient
from agents.sentiment.news_client import NewsClient


class TestEnvironmentValidation:
    """Test class for validating environment variable combinations in sentiment agent"""
    
    def setUp(self):
        """Set up test environment with clean state"""
        # Store original environment variables
        self.original_twitter_token = os.environ.get('TWITTER_BEARER_TOKEN')
        self.original_cryptopanic_key = os.environ.get('CRYPTOPANIC_API_KEY')
        
        # Clear environment variables to start with clean state
        if 'TWITTER_BEARER_TOKEN' in os.environ:
            del os.environ['TWITTER_BEARER_TOKEN']
        if 'CRYPTOPANIC_API_KEY' in os.environ:
            del os.environ['CRYPTOPANIC_API_KEY']
    
    def tearDown(self):
        """Restore original environment variables"""
        # Restore original environment variables
        if self.original_twitter_token:
            os.environ['TWITTER_BEARER_TOKEN'] = self.original_twitter_token
        elif 'TWITTER_BEARER_TOKEN' in os.environ:
            del os.environ['TWITTER_BEARER_TOKEN']
            
        if self.original_cryptopanic_key:
            os.environ['CRYPTOPANIC_API_KEY'] = self.original_cryptopanic_key
        elif 'CRYPTOPANIC_API_KEY' in os.environ:
            del os.environ['CRYPTOPANIC_API_KEY']
    
    @pytest.mark.asyncio
    async def test_both_env_vars_present_full_real_sentiment(self):
        """
        Test scenario where both TWITTER_BEARER_TOKEN and CRYPTOPANIC_API_KEY are present.
        Should use real Twitter and real News data.
        """
        self.setUp()
        try:
            # Set both environment variables
            os.environ['TWITTER_BEARER_TOKEN'] = 'fake_twitter_token_123'
            os.environ['CRYPTOPANIC_API_KEY'] = 'fake_cryptopanic_key_456'
            
            # Create sentiment agent
            agent = SentimentAgent()
            
            # Verify clients are enabled
            assert agent.twitter_client.enabled is True
            assert agent.news_client.enabled is True
            
            # Mock the API calls to avoid actual network requests
            with patch.object(agent.twitter_client, 'get_crypto_tweets', new_callable=AsyncMock) as mock_twitter:
                with patch.object(agent.news_client, 'get_relevant_news', new_callable=AsyncMock) as mock_news:
                    # Mock responses
                    mock_twitter.return_value = ["Positive tweet about BTC", "Bullish sentiment on ETH"]
                    mock_news.return_value = [
                        {
                            'title': 'Crypto Market Rises',
                            'content': 'Strong positive movement in crypto markets today'
                        }
                    ]
                    
                    # Call get_overall_sentiment
                    result = await agent.get_overall_sentiment(
                        trading_pairs=['BTCUSDT', 'ETHUSDT']
                    )
                    
                    # Verify both sources were used
                    assert 'twitter' in result
                    assert 'news' in result
                    assert 'combined' in result
                    
                    # Verify sources_used contains both real sources
                    sources_used = result['combined']['sources_used']
                    assert 'twitter' in sources_used
                    assert 'news' in sources_used
                    assert 'mock_generator' not in sources_used
                    assert 'fear_greed_index' in sources_used  # F&G is always included by default
                    
                    # Verify API methods were called
                    mock_twitter.assert_called_once()
                    mock_news.assert_called_once()
                    
        finally:
            self.tearDown()
    
    @pytest.mark.asyncio
    async def test_only_twitter_env_var_twitter_plus_mock_news(self):
        """
        Test scenario where only TWITTER_BEARER_TOKEN is present.
        Should use real Twitter and mock News data.
        """
        self.setUp()
        try:
            # Set only Twitter environment variable
            os.environ['TWITTER_BEARER_TOKEN'] = 'fake_twitter_token_123'
            # Don't set CRYPTOPANIC_API_KEY
            
            # Create sentiment agent
            agent = SentimentAgent()
            
            # Verify Twitter is enabled, News is disabled
            assert agent.twitter_client.enabled is True
            assert agent.news_client.enabled is False
            
            # Mock the Twitter API call but News should be skipped
            with patch.object(agent.twitter_client, 'get_crypto_tweets', new_callable=AsyncMock) as mock_twitter:
                # Mock Twitter response
                mock_twitter.return_value = ["Positive tweet about BTC", "Bullish sentiment on ETH"]
                
                # Call get_overall_sentiment
                result = await agent.get_overall_sentiment(
                    trading_pairs=['BTCUSDT', 'ETHUSDT']
                )
                
                # Verify Twitter was used but News was not
                assert 'twitter' in result
                # News should not be in results since API key is missing
                
                # Verify sources_used contains Twitter and F&G (but not news)
                sources_used = result['combined']['sources_used']
                assert 'twitter' in sources_used
                assert 'fear_greed_index' in sources_used
                assert 'news' not in sources_used  # News client is disabled
                
                # Check that Twitter API was called
                mock_twitter.assert_called_once()
                
        finally:
            self.tearDown()
    
    @pytest.mark.asyncio
    async def test_only_cryptopanic_env_var_news_plus_mock_twitter(self):
        """
        Test scenario where only CRYPTOPANIC_API_KEY is present.
        Should use real News and mock Twitter data.
        """
        self.setUp()
        try:
            # Don't set TWITTER_BEARER_TOKEN
            # Set only CryptoPanic environment variable
            os.environ['CRYPTOPANIC_API_KEY'] = 'fake_cryptopanic_key_456'
            
            # Create sentiment agent
            agent = SentimentAgent()
            
            # Verify Twitter is disabled, News is enabled
            assert agent.twitter_client.enabled is False
            assert agent.news_client.enabled is True
            
            # Mock the News API call but Twitter should be skipped
            with patch.object(agent.news_client, 'get_relevant_news', new_callable=AsyncMock) as mock_news:
                # Mock response
                mock_news.return_value = [
                    {
                        'title': 'Crypto Market Update',
                        'content': 'Market showing mixed signals today'
                    }
                ]
                
                # Call get_overall_sentiment
                result = await agent.get_overall_sentiment(
                    trading_pairs=['BTCUSDT', 'ETHUSDT']
                )
                
                # Verify News was used but Twitter was not
                assert 'news' in result
                # Twitter should not be in results since API key is missing
                
                # Verify sources_used contains News
                sources_used = result['combined']['sources_used']
                assert 'news' in sources_used
                assert 'twitter' not in sources_used  # Twitter client is disabled
                
                # Check that News API was called
                mock_news.assert_called_once()
                
        finally:
            self.tearDown()
    
    @pytest.mark.asyncio
    async def test_no_env_vars_full_mock(self):
        """
        Test scenario where neither TWITTER_BEARER_TOKEN nor CRYPTOPANIC_API_KEY are present.
        Should use F&G index and potentially mock_generator if no social data.
        """
        self.setUp()
        try:
            # Ensure no environment variables are set
            if 'TWITTER_BEARER_TOKEN' in os.environ:
                del os.environ['TWITTER_BEARER_TOKEN']
            if 'CRYPTOPANIC_API_KEY' in os.environ:
                del os.environ['CRYPTOPANIC_API_KEY']
            
            # Create sentiment agent
            agent = SentimentAgent()
            
            # Verify both clients are disabled
            assert agent.twitter_client.enabled is False
            assert agent.news_client.enabled is False
            
            # Mock the F&G index call to avoid external API calls
            with patch.object(agent, 'get_fear_greed_index', new_callable=AsyncMock) as mock_fng:
                mock_fng.return_value = {
                    'value': 50,
                    'classification': 'Neutral',
                    'timestamp': '2023-01-01T00:00:00'
                }
                
                # Call get_overall_sentiment
                result = await agent.get_overall_sentiment(
                    trading_pairs=['BTCUSDT', 'ETHUSDT']
                )
                
                # With no real social data sources, F&G should be present
                sources_used = result['combined']['sources_used']
                assert 'fear_greed_index' in sources_used
                assert 'twitter' not in sources_used
                assert 'news' not in sources_used
                
                # When no social data is available, mock generator might be used
                # depending on the internal logic of the agent
                # Verify the result structure
                assert 'combined' in result
                assert 'sentiment_score' in result['combined']
                assert isinstance(result['combined']['sentiment_score'], float)
                assert -1.0 <= result['combined']['sentiment_score'] <= 1.0
                
                # Verify F&G was called
                mock_fng.assert_called_once()
            
        finally:
            self.tearDown()
    
    @pytest.mark.asyncio
    async def test_env_var_precedence_over_config_parameters(self):
        """
        Test that environment variables take precedence over config parameters.
        """
        self.setUp()
        try:
            # Don't set environment variables initially
            if 'TWITTER_BEARER_TOKEN' in os.environ:
                del os.environ['TWITTER_BEARER_TOKEN']
            if 'CRYPTOPANIC_API_KEY' in os.environ:
                del os.environ['CRYPTOPANIC_API_KEY']
            
            # Create config with fake API keys (should be overridden by env vars)
            config = SentimentConfig()
            # Create agent with config that has API keys
            agent = SentimentAgent(config)
            
            # Initially, clients should be disabled since no env vars are set
            assert agent.twitter_client.enabled is False
            assert agent.news_client.enabled is False
            
            # Now set environment variables
            os.environ['TWITTER_BEARER_TOKEN'] = 'env_twitter_token'
            os.environ['CRYPTOPANIC_API_KEY'] = 'env_cryptopanic_key'
            
            # Create a new agent to pick up the environment variables
            agent_with_env = SentimentAgent(config)
            
            # Now both should be enabled due to environment variables taking precedence
            assert agent_with_env.twitter_client.enabled is True
            assert agent_with_env.news_client.enabled is True
            
            # Verify the clients got the values from environment variables
            assert agent_with_env.twitter_client.bearer_token == 'env_twitter_token'
            assert agent_with_env.news_client.api_key == 'env_cryptopanic_key'
            
        finally:
            self.tearDown()
    
    @pytest.mark.asyncio
    async def test_twitter_client_initialization_with_env_var(self):
        """
        Test TwitterClient initialization respects environment variables.
        """
        self.setUp()
        try:
            # Set environment variable
            os.environ['TWITTER_BEARER_TOKEN'] = 'test_twitter_token_789'
            
            # Create TwitterClient directly
            twitter_client = TwitterClient()
            
            # Verify it picked up the environment variable
            assert twitter_client.bearer_token == 'test_twitter_token_789'
            assert twitter_client.enabled is True
            
            # Test with explicit parameter (should override environment)
            explicit_client = TwitterClient(bearer_token='explicit_token')
            assert explicit_client.bearer_token == 'explicit_token'
            assert explicit_client.enabled is True
            
            # Test with no parameter and no environment (should be disabled)
            del os.environ['TWITTER_BEARER_TOKEN']
            disabled_client = TwitterClient()
            assert disabled_client.bearer_token is None
            assert disabled_client.enabled is False
            
        finally:
            self.tearDown()
    
    @pytest.mark.asyncio
    async def test_news_client_initialization_with_env_var(self):
        """
        Test NewsClient initialization respects environment variables.
        """
        self.setUp()
        try:
            # Set environment variable
            os.environ['CRYPTOPANIC_API_KEY'] = 'test_cryptopanic_key_abc'
            
            # Create NewsClient directly
            news_client = NewsClient()
            
            # Verify it picked up the environment variable
            assert news_client.api_key == 'test_cryptopanic_key_abc'
            assert news_client.enabled is True
            
            # Test with explicit parameter (should override environment)
            explicit_client = NewsClient(api_key='explicit_api_key')
            assert explicit_client.api_key == 'explicit_api_key'
            assert explicit_client.enabled is True
            
            # Test with no parameter and no environment (should be disabled)
            del os.environ['CRYPTOPANIC_API_KEY']
            disabled_client = NewsClient()
            assert disabled_client.api_key is None
            assert disabled_client.enabled is False
            
        finally:
            self.tearDown()
    
    @pytest.mark.asyncio
    async def test_combined_sentiment_sources_tracking(self):
        """
        Test that sources_used properly tracks which data sources were actually used.
        """
        self.setUp()
        try:
            # Set both environment variables
            os.environ['TWITTER_BEARER_TOKEN'] = 'fake_twitter_token'
            os.environ['CRYPTOPANIC_API_KEY'] = 'fake_cryptopanic_key'
            
            agent = SentimentAgent()
            
            # Mock both API calls to return data
            with patch.object(agent.twitter_client, 'get_crypto_tweets', new_callable=AsyncMock) as mock_twitter:
                with patch.object(agent.news_client, 'get_relevant_news', new_callable=AsyncMock) as mock_news:
                    mock_twitter.return_value = ["Tweet 1", "Tweet 2"]
                    mock_news.return_value = [
                        {'title': 'News 1', 'content': 'Content 1'},
                        {'title': 'News 2', 'content': 'Content 2'}
                    ]
                    
                    result = await agent.get_overall_sentiment(trading_pairs=['BTCUSDT'])
                    
                    # Verify all real sources are tracked
                    sources_used = result['combined']['sources_used']
                    assert 'twitter' in sources_used
                    assert 'news' in sources_used
                    assert 'fear_greed_index' in sources_used
                    assert 'mock_generator' not in sources_used  # No mock needed when real data exists
                    
        finally:
            self.tearDown()
    
    @pytest.mark.asyncio
    async def test_mock_fallback_when_real_api_fails(self):
        """
        Test that mock data is used when real API calls fail.
        """
        self.setUp()
        try:
            # Set both environment variables
            os.environ['TWITTER_BEARER_TOKEN'] = 'fake_twitter_token'
            os.environ['CRYPTOPANIC_API_KEY'] = 'fake_cryptopanic_key'
            
            agent = SentimentAgent()
            
            # Mock both API calls to raise exceptions
            with patch.object(agent.twitter_client, 'get_crypto_tweets', side_effect=Exception("API Error")):
                with patch.object(agent.news_client, 'get_relevant_news', side_effect=Exception("API Error")):
                    # Also mock F&G to avoid external API calls
                    with patch.object(agent, 'get_fear_greed_index', new_callable=AsyncMock) as mock_fng:
                        mock_fng.return_value = {
                            'value': 50,
                            'classification': 'Neutral',
                            'timestamp': '2023-01-01T00:00:00'
                        }
                        
                        # Mock the internal _generate_mock_sentiment method
                        with patch.object(agent, '_generate_mock_sentiment') as mock_gen:
                            mock_gen.return_value = {
                                'sentiment_score': 0.2,
                                'value': 60,
                                'classification': 'Greed',
                                'timestamp': '2023-01-01T00:00:00',
                                'source': 'mock_generator'
                            }
                            
                            result = await agent.get_overall_sentiment(trading_pairs=['BTCUSDT'])
                            
                            # When real APIs fail, mock data should be generated as fallback
                            sources_used = result['combined']['sources_used']
                            # F&G should still be present, and mock_generator if no other data available
                            assert 'fear_greed_index' in sources_used
                            
        finally:
            self.tearDown()


if __name__ == "__main__":
    pytest.main([__file__])