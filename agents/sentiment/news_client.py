"""
CryptoPanic News API client for fetching crypto-specific news
"""

import os
import logging
from typing import List, Dict, Optional
import httpx
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class NewsClient:
    """
    CryptoPanic API client for fetching cryptocurrency news with sentiment data.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize News client.
        
        Args:
            api_key: CryptoPanic API key. If not provided, reads from CRYPTOPANIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('CRYPTOPANIC_API_KEY')
        self.base_url = "https://cryptopanic.com/api/v1/posts/"
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.warning("CryptoPanic API key not found. News sentiment will be disabled.")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException))
    )
    async def get_crypto_news(self, currencies: List[str], hours_back: int = 24) -> List[Dict]:
        """
        Fetch crypto-specific news articles.
        
        Args:
            currencies: List of currency symbols (e.g., ["BTC", "ETH"])
            hours_back: How many hours back to fetch news (default: 24)
            
        Returns:
            List[Dict]: List of news articles with title, content, source, and metadata
        """
        if not self.enabled:
            return []
        
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        cutoff_str = cutoff_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Build query parameters
        params = {
            "auth_token": self.api_key,
            "currencies": ",".join(currencies),
            "kind": "news",
            "public": "true",
            "filter": "hot",  # Focus on trending/hot news
            "limit": 50
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, params=params)
                
                if response.status_code == 401:  # Unauthorized
                    logger.error("CryptoPanic API unauthorized. Check API key.")
                    self.enabled = False
                    return []
                elif response.status_code != 200:
                    response.raise_for_status()
                
                data = response.json()
                articles = []
                
                if 'results' in data:
                    for item in data['results']:
                        # Filter by published time
                        published_at = item.get('published_at')
                        if published_at and published_at >= cutoff_str:
                            article = {
                                'title': item.get('title', ''),
                                'content': item.get('body', '') or item.get('description', ''),
                                'source': item.get('domain', 'cryptopanic'),
                                'url': item.get('url', ''),
                                'published_at': published_at,
                                'currencies': [curr['code'] for curr in item.get('currencies', [])]
                            }
                            articles.append(article)
                
                logger.info(f"Fetched {len(articles)} news articles for currencies: {currencies}")
                return articles
                
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            return []
    
    async def get_relevant_news(self, trading_pairs: List[str]) -> List[Dict]:
        """
        Get news relevant to trading pairs.
        
        Args:
            trading_pairs: List of trading pairs (e.g., ["BTCUSDT", "ETHUSDT"])
            
        Returns:
            List[Dict]: List of relevant news articles
        """
        if not self.enabled:
            return []
        
        currencies = []
        for pair in trading_pairs:
            if pair.endswith('USDT'):
                currencies.append(pair[:-4])
            else:
                currencies.append(pair.split('USDT')[0] if 'USDT' in pair else pair)
        
        seen = set()
        unique_currencies = []
        for curr in currencies:
            if curr not in seen:
                seen.add(curr)
                unique_currencies.append(curr)
        
        if not unique_currencies:
            return []
        
        return await self.get_crypto_news(unique_currencies, hours_back=24)