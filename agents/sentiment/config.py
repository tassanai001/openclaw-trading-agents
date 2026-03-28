"""
Configuration for Sentiment Analysis Agent
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class SentimentConfig:
    """
    Configuration class for Sentiment Agent
    """
    twitter_weight: float = 0.4
    news_weight: float = 0.6
    use_real_sentiment: bool = True
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_bearer_token: Optional[str] = None
    cryptopanic_api_key: Optional[str] = None
    api_key: Optional[str] = None
    timeout: int = 30
    retries: int = 3
    
    def __post_init__(self):
        """Validate configuration values and load from environment if not provided"""
        if not 0 <= self.twitter_weight <= 1:
            raise ValueError("twitter_weight must be between 0 and 1")
        if not 0 <= self.news_weight <= 1:
            raise ValueError("news_weight must be between 0 and 1")
        if self.twitter_weight + self.news_weight != 1.0:
            # Normalize weights to sum to 1
            total_weight = self.twitter_weight + self.news_weight
            if total_weight > 0:
                self.twitter_weight /= total_weight
                self.news_weight /= total_weight
        
        if self.twitter_bearer_token is None:
            self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        if self.cryptopanic_api_key is None:
            self.cryptopanic_api_key = os.getenv('CRYPTOPANIC_API_KEY')
        
        use_real_env = os.getenv('USE_REAL_SENTIMENT')
        if use_real_env is not None:
            self.use_real_sentiment = use_real_env.lower() in ('true', '1', 'yes', 'on')