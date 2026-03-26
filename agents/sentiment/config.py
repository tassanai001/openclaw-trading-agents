"""
Configuration for Sentiment Analysis Agent
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SentimentConfig:
    """
    Configuration class for Sentiment Agent
    """
    # Weight for Twitter sentiment in combined analysis
    twitter_weight: float = 0.4
    
    # Weight for News sentiment in combined analysis
    news_weight: float = 0.6
    
    # API key for sentiment service (if using external service)
    api_key: Optional[str] = None
    
    # Default timeout for API calls
    timeout: int = 30
    
    # Number of retries for failed requests
    retries: int = 3
    
    def __post_init__(self):
        """Validate configuration values"""
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