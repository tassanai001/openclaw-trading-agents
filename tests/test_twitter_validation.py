"""
Tests for Twitter Bearer Token Validation

This test file validates TWITTER_BEARER_TOKEN functionality including:
- Valid token enables Twitter sentiment
- Invalid/missing token falls back gracefully
- Authentication errors handled properly
- Rate limit handling tested
"""

import os
import pytest
import asyncio
import httpx
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from agents.sentiment.twitter_client import TwitterClient
from agents.sentiment.sentiment import SentimentAgent
from agents.sentiment.config import SentimentConfig


class TestTwitterValidation:
    """Test class for validating Twitter Bearer Token functionality"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Store original environment variable
        self.original_token = os.environ.get('TWITTER_BEARER_TOKEN')
        
    def tearDown(self):
        """Clean up after each test method."""
        # Restore original environment variable
        if self.original_token is not None:
            os.environ['TWITTER_BEARER_TOKEN'] = self.original_token
        elif 'TWITTER_BEARER_TOKEN' in os.environ:
            del os.environ['TWITTER_BEARER_TOKEN']
    
    @pytest.mark.asyncio
    async def test_valid_token_enables_twitter_client(self):
        """Test that a valid token enables the Twitter client functionality."""
        # Arrange
        valid_token = "valid_bearer_token_12345"
        
        # Act
        with patch.dict(os.environ, {'TWITTER_BEARER_TOKEN': valid_token}):
            twitter_client = TwitterClient()
            
        # Assert
        assert twitter_client.enabled is True
        assert twitter_client.bearer_token == valid_token
    
    @pytest.mark.asyncio
    async def test_missing_token_disables_twitter_client(self):
        """Test that missing token disables Twitter client and falls back gracefully."""
        # Arrange
        if 'TWITTER_BEARER_TOKEN' in os.environ:
            del os.environ['TWITTER_BEARER_TOKEN']
        
        # Act
        twitter_client = TwitterClient()
        
        # Assert
        assert twitter_client.enabled is False
        assert twitter_client.bearer_token is None
    
    @pytest.mark.asyncio
    async def test_token_passed_as_parameter(self):
        """Test that token passed as parameter takes precedence over environment variable."""
        # Arrange
        env_token = "env_token_123"
        param_token = "param_token_456"
        
        # Act
        with patch.dict(os.environ, {'TWITTER_BEARER_TOKEN': env_token}):
            twitter_client = TwitterClient(bearer_token=param_token)
        
        # Assert
        assert twitter_client.enabled is True
        assert twitter_client.bearer_token == param_token
    
    @pytest.mark.asyncio
    async def test_invalid_token_authentication_error(self):
        """Test that invalid token results in authentication error handling."""
        # Arrange
        invalid_token = "invalid_token_123"
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = '{"error": "Unauthorized"}'
        
        # Act & Assert
        with patch.dict(os.environ, {'TWITTER_BEARER_TOKEN': invalid_token}):
            twitter_client = TwitterClient()
            
            with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_response
                
                result = await twitter_client.search_tweets("$BTC")
                
                # Should return empty list due to authentication failure
                assert result == []
                # Client should be disabled after auth failure
                assert twitter_client.enabled is False
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test that rate limit scenarios are handled properly."""
        # Arrange
        valid_token = "valid_token_123"
        mock_response = MagicMock()
        mock_response.status_code = 429  # Rate limited
        mock_response.headers = {
            'x-rate-limit-remaining': '0',
            'x-rate-limit-reset': '1234567890'
        }
        mock_response.text = '{"error": "Rate limit exceeded"}'
        
        # Act & Assert
        with patch.dict(os.environ, {'TWITTER_BEARER_TOKEN': valid_token}):
            twitter_client = TwitterClient()
            
            with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_response
                
                result = await twitter_client.search_tweets("$BTC")
                
                # Should return empty list due to rate limit
                assert result == []
                # Rate limit values should be updated
                assert twitter_client.rate_limit_remaining == 0
                assert twitter_client.rate_limit_reset == 1234567890
    
    @pytest.mark.asyncio
    async def test_successful_api_call_with_valid_token(self):
        """Test that successful API call works with valid token."""
        # Arrange
        valid_token = "valid_token_123"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {
            'x-rate-limit-remaining': '449',
            'x-rate-limit-reset': '1234567890'
        }
        mock_response.json.return_value = {
            'data': [
                {'text': 'Bitcoin is going to the moon!', 'lang': 'en', 'public_metrics': {'like_count': 15}},
                {'text': 'Crypto market looks bullish today', 'lang': 'en', 'public_metrics': {'like_count': 20}}
            ]
        }
        
        # Act & Assert
        with patch.dict(os.environ, {'TWITTER_BEARER_TOKEN': valid_token}):
            twitter_client = TwitterClient()
            
            with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_response
                
                result = await twitter_client.search_tweets("$BTC")
                
                # Should return the tweets
                assert len(result) == 2
                assert 'Bitcoin is going to the moon!' in result
                assert 'Crypto market looks bullish today' in result
                # Rate limit values should be updated
                assert twitter_client.rate_limit_remaining == 449
                assert twitter_client.rate_limit_reset == 1234567890
    
    @pytest.mark.asyncio
    async def test_twitter_fallback_when_disabled(self):
        """Test that sentiment agent falls back gracefully when Twitter is disabled."""
        # Arrange
        if 'TWITTER_BEARER_TOKEN' in os.environ:
            del os.environ['TWITTER_BEARER_TOKEN']
        
        # Act
        sentiment_agent = SentimentAgent()
        
        # Assert
        # With no token, Twitter should be disabled
        assert sentiment_agent.config.twitter_weight == 0.4  # Default weight
        
        # When Twitter is disabled, it should return empty results
        result = await sentiment_agent.analyze_twitter_sentiment([])
        assert result['sentiment_score'] == 0.0  # Should default to neutral when no data
        assert result['total_tweets'] == 0
        assert result['source'] == 'twitter'
    
    @pytest.mark.asyncio
    async def test_twitter_client_handles_server_errors(self):
        """Test that Twitter client handles server errors gracefully."""
        valid_token = "valid_token_123"
        
        # Mock a server error response
        error_response = AsyncMock()
        error_response.status_code = 500
        error_response.raise_for_status.side_effect = httpx.HTTPError("Server Error")
        
        with patch.dict(os.environ, {'TWITTER_BEARER_TOKEN': valid_token}):
            twitter_client = TwitterClient()
            
            with patch('httpx.AsyncClient.get', return_value=error_response):
                result = await twitter_client.search_tweets("$BTC")
                
                # With server error, should return empty list
                assert result == []
    
    @pytest.mark.asyncio
    async def test_multiple_crypto_symbols_search(self):
        """Test searching for multiple crypto symbols with Twitter client."""
        # Arrange
        valid_token = "valid_token_123"
        btc_response = AsyncMock(
            status_code=200,
            json=lambda: {
                'data': [
                    {'text': 'Bitcoin rally continues', 'lang': 'en', 'public_metrics': {'like_count': 25}}
                ]
            },
            headers={'x-rate-limit-remaining': '447', 'x-rate-limit-reset': '1234567890'}
        )
        eth_response = AsyncMock(
            status_code=200,
            json=lambda: {
                'data': [
                    {'text': 'Ethereum breaking resistance', 'lang': 'en', 'public_metrics': {'like_count': 30}}
                ]
            },
            headers={'x-rate-limit-remaining': '446', 'x-rate-limit-reset': '1234567890'}
        )
        
        # Act & Assert
        with patch.dict(os.environ, {'TWITTER_BEARER_TOKEN': valid_token}):
            twitter_client = TwitterClient()
            
            with patch('httpx.AsyncClient.get', side_effect=[btc_response, eth_response]) as mock_get:
                result = await twitter_client.get_crypto_tweets(["BTC", "ETH"])
                
                # Should return tweets from both symbols
                assert len(result) == 2
                assert 'Bitcoin rally continues' in result
                assert 'Ethereum breaking resistance' in result
    
    @pytest.mark.asyncio
    async def test_config_loads_token_from_environment(self):
        """Test that SentimentConfig properly loads token from environment."""
        # Arrange
        token = "config_token_123"
        
        # Act
        with patch.dict(os.environ, {'TWITTER_BEARER_TOKEN': token}):
            config = SentimentConfig()
        
        # Assert
        assert config.twitter_bearer_token == token
    
    @pytest.mark.asyncio
    async def test_config_handles_missing_token_gracefully(self):
        """Test that SentimentConfig handles missing token gracefully."""
        # Arrange
        if 'TWITTER_BEARER_TOKEN' in os.environ:
            del os.environ['TWITTER_BEARER_TOKEN']
        
        # Act
        config = SentimentConfig()
        
        # Assert
        assert config.twitter_bearer_token is None
        # Twitter should still be enabled by default, but client will be disabled
        assert config.twitter_weight == 0.4