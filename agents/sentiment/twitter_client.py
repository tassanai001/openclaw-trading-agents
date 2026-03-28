"""
Twitter API v2 client for fetching crypto-related tweets
"""

import os
import logging
import asyncio
from typing import List, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class TwitterClient:
    """
    Twitter API v2 client for fetching recent tweets about cryptocurrencies.
    Uses Essential/Elevated access level with rate limit handling.
    """
    
    def __init__(self, bearer_token: Optional[str] = None):
        """
        Initialize Twitter client.
        
        Args:
            bearer_token: Twitter API Bearer Token. If not provided, reads from TWITTER_BEARER_TOKEN env var.
        """
        self.bearer_token = bearer_token or os.getenv('TWITTER_BEARER_TOKEN')
        self.base_url = "https://api.twitter.com/2"
        self.rate_limit_remaining = 450  # Default rate limit for Essential access
        self.rate_limit_reset = 0
        
        if not self.bearer_token:
            logger.warning("Twitter Bearer Token not found. Twitter sentiment will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException))
    )
    async def search_tweets(self, query: str, max_results: int = 100) -> List[str]:
        """
        Search recent tweets by query.
        
        Args:
            query: Search query (e.g., "$BTC", "bitcoin")
            max_results: Maximum number of tweets to return (10-100)
            
        Returns:
            List[str]: List of tweet texts
            
        Note:
            - Filters: English only, no retweets, min 10 likes
            - Handles rate limits automatically
        """
        if not self.enabled:
            return []
        
        # Validate max_results
        max_results = max(10, min(100, max_results))
        
        # Build search query with filters
        full_query = f"{query} lang:en -is:retweet min_faves:10"
        
        url = f"{self.base_url}/tweets/search/recent"
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "OpenClaw-Trading-Agents/1.0"
        }
        params = {
            "query": full_query,
            "max_results": max_results,
            "tweet.fields": "public_metrics,lang,created_at",
            "expansions": "author_id",
            "user.fields": "public_metrics"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers, params=params)
                
                # Handle rate limiting
                if 'x-rate-limit-remaining' in response.headers:
                    self.rate_limit_remaining = int(response.headers['x-rate-limit-remaining'])
                if 'x-rate-limit-reset' in response.headers:
                    self.rate_limit_reset = int(response.headers['x-rate-limit-reset'])
                
                if response.status_code == 429:  # Rate limited
                    logger.warning(f"Twitter API rate limited. Reset at: {self.rate_limit_reset}")
                    return []
                elif response.status_code == 401:  # Unauthorized
                    logger.error("Twitter API unauthorized. Check Bearer Token.")
                    self.enabled = False
                    return []
                elif response.status_code != 200:
                    response.raise_for_status()
                
                data = response.json()
                tweets = []
                
                if 'data' in data:
                    for tweet in data['data']:
                        # Additional filtering for English and like count
                        if (tweet.get('lang', 'en') == 'en' and 
                            tweet.get('public_metrics', {}).get('like_count', 0) >= 10):
                            tweets.append(tweet['text'])
                
                logger.info(f"Fetched {len(tweets)} tweets for query: {query}")
                return tweets
                
        except Exception as e:
            logger.error(f"Error fetching tweets: {e}")
            return []
    
    async def get_crypto_tweets(self, symbols: List[str], max_results: int = 100) -> List[str]:
        """
        Get tweets for multiple crypto symbols.
        
        Args:
            symbols: List of crypto symbols (e.g., ["BTC", "ETH"])
            max_results: Maximum results per symbol
            
        Returns:
            List[str]: Combined list of tweet texts
        """
        if not self.enabled:
            return []
        
        all_tweets = []
        tasks = []
        
        # Create cashtag queries ($BTC, $ETH, etc.)
        for symbol in symbols:
            cashtag = f"${symbol}"
            tasks.append(self.search_tweets(cashtag, max_results // len(symbols) if symbols else max_results))
        
        # Execute queries concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    all_tweets.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Error in tweet search: {result}")
        
        # Deduplicate tweets
        unique_tweets = list(set(all_tweets))
        return unique_tweets[:max_results]