"""
Sentiment Analysis Agent
Analyzes Twitter and News sentiment using real APIs and NLP model, returns score between -1 and 1
"""

import asyncio
import random
import logging
import numpy as np
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from .config import SentimentConfig
from .nlp_analyzer import NLPSentimentAnalyzer
from .twitter_client import TwitterClient
from .news_client import NewsClient


class SentimentAgent:
    """
    Agent that analyzes Twitter and News sentiment to return a score between -1 and 1
    """
    
    def __init__(self, config: Optional[SentimentConfig] = None):
        self.config = config or SentimentConfig()
        self._twitter_sources = []
        self._news_sources = []
        self.logger = logging.getLogger(__name__)
        
        self.nlp_analyzer = NLPSentimentAnalyzer()
        self.twitter_client = TwitterClient()
        self.news_client = NewsClient()
        self.use_real_sentiment = getattr(self.config, 'use_real_sentiment', True)
        
    async def analyze(self, text: str) -> float:
        """
        Analyze sentiment of given text and return score between -1 and 1
        
        Args:
            text: Text to analyze
            
        Returns:
            float: Sentiment score between -1 (very negative) and 1 (very positive)
        """
        # Simple mock implementation - in real scenario would use NLP model
        score = await self._analyze_sentiment(text)
        return max(-1.0, min(1.0, score))
        
    async def analyze_twitter_sentiment(self, tweets: List[str]) -> Dict:
        """
        Analyze sentiment from Twitter data
        
        Args:
            tweets: List of tweet texts
            
        Returns:
            Dict: Analysis results with average score and metadata
        """
        scores = []
        for tweet in tweets:
            score = await self._analyze_sentiment(tweet)
            scores.append(score)
            
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            'sentiment_score': avg_score,
            'total_tweets': len(tweets),
            'timestamp': datetime.now().isoformat(),
            'source': 'twitter'
        }
    
    async def analyze_news_sentiment(self, articles: List[Dict]) -> Dict:
        """
        Analyze sentiment from news articles
        
        Args:
            articles: List of news articles with 'title' and 'content' keys
            
        Returns:
            Dict: Analysis results with average score and metadata
        """
        scores = []
        for article in articles:
            title = article.get('title', '')
            content = article.get('content', '')
            text = f"{title} {content}"
            score = await self._analyze_sentiment(text)
            scores.append(score)
            
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            'sentiment_score': avg_score,
            'total_articles': len(articles),
            'timestamp': datetime.now().isoformat(),
            'source': 'news'
        }
    
    async def _fetch_real_sentiment_data(self, trading_pairs: Optional[List[str]] = None) -> tuple:
        """
        Fetch real Twitter and News data using API clients.
        
        Args:
            trading_pairs: List of trading pairs to fetch data for
            
        Returns:
            tuple: (twitter_tweets, news_articles)
        """
        if not self.use_real_sentiment:
            return [], []
            
        twitter_tweets = []
        news_articles = []
        
        try:
            if self.twitter_client.enabled and trading_pairs:
                symbols = [pair.replace('USDT', '') for pair in trading_pairs]
                twitter_tweets = await self.twitter_client.get_crypto_tweets(symbols, max_results=50)
        except Exception as e:
            self.logger.error(f"Error fetching Twitter data: {e}")
            
        try:
            if self.news_client.enabled and trading_pairs:
                news_articles = await self.news_client.get_relevant_news(trading_pairs)
        except Exception as e:
            self.logger.error(f"Error fetching News data: {e}")
            
        return twitter_tweets, news_articles
    
    async def get_overall_sentiment(self, twitter_data: Optional[List[str]] = None, 
                                  news_data: Optional[List[Dict]] = None,
                                  include_fng: bool = True,
                                  trading_pairs: Optional[List[str]] = None) -> Dict:
        """
        Get overall sentiment combining Twitter, News, and Fear & Greed Index
        
        Args:
            twitter_data: List of tweets (if None, fetches real data when enabled)
            news_data: List of news articles (if None, fetches real data when enabled)
            include_fng: Whether to include Fear & Greed Index
            trading_pairs: Trading pairs to fetch data for (required when fetching real data)
            
        Returns:
            Dict: Combined sentiment analysis
        """
        results = {}
        
        if (twitter_data is None or news_data is None) and self.use_real_sentiment:
            fetched_twitter, fetched_news = await self._fetch_real_sentiment_data(trading_pairs)
            if twitter_data is None:
                twitter_data = fetched_twitter
            if news_data is None:
                news_data = fetched_news
        
        has_social_data = (twitter_data and len(twitter_data) > 0) or (news_data and len(news_data) > 0)
        
        if twitter_data and len(twitter_data) > 0:
            results['twitter'] = await self.analyze_twitter_sentiment(twitter_data)
            
        if news_data and len(news_data) > 0:
            results['news'] = await self.analyze_news_sentiment(news_data)
        
        fng_data = None
        has_fng = False
        if include_fng:
            fng_data = await self.get_fear_greed_index()
            if fng_data and 'error' not in fng_data:
                fng_sentiment = (fng_data['value'] - 50) / 50.0
                results['fng'] = {
                    'sentiment_score': fng_sentiment,
                    'value': fng_data['value'],
                    'classification': fng_data['classification'],
                    'timestamp': datetime.now().isoformat(),
                    'source': 'fear_greed_index'
                }
                has_fng = True
            
        if not self.use_real_sentiment and not has_social_data and not has_fng:
            results['mock'] = self._generate_mock_sentiment()
        
        # When only one source, return that source's score
        if len(results) == 1:
            for key in results:
                if key != 'combined':
                    combined_score = results[key]['sentiment_score']
                    break
        else:
            # Multiple sources - calculate weighted average
            sources_count = 0
            weighted_sum = 0.0
            
            if 'fng' in results:
                weighted_sum += results['fng']['sentiment_score'] * 0.4
                sources_count += 0.4
            
            if 'twitter' in results:
                twitter_weight = self.config.twitter_weight
                weighted_sum += results['twitter']['sentiment_score'] * twitter_weight
                sources_count += twitter_weight
            
            if 'news' in results:
                news_weight = self.config.news_weight
                weighted_sum += results['news']['sentiment_score'] * news_weight
                sources_count += news_weight
            
            if 'mock' in results:
                weighted_sum += results['mock']['sentiment_score'] * 0.5
                sources_count += 0.5
            
            if sources_count > 0:
                combined_score = weighted_sum / sources_count
            else:
                combined_score = 0.0
        
        # Build sources used list
        sources_used = []
        if 'twitter' in results:
            sources_used.append('twitter')
        if 'news' in results:
            sources_used.append('news')
        if 'fng' in results:
            sources_used.append('fear_greed_index')
        if 'mock' in results:
            sources_used.append('mock_generator')
        
        results['combined'] = {
            'sentiment_score': round(combined_score, 3),
            'timestamp': datetime.now().isoformat(),
            'sources_used': sources_used
        }
        
        return results
    
    def _generate_mock_sentiment(self) -> Dict:
        """Generate diverse mock sentiment when no real data is available"""
        # Use time-based seed for diversity
        import time
        minute_of_day = int(time.time() / 60) % (24 * 60)
        
        # Create cyclical patterns (different times have different sentiment)
        base_sentiment = np.sin(minute_of_day / (4 * 60) * np.pi) * 0.4
        
        # Add some variation based on hash of current date
        day_hash = hash(datetime.now().date()) % 100
        day_variation = (day_hash - 50) / 125.0
        
        # Add random noise
        noise = random.uniform(-0.15, 0.15)
        
        score = base_sentiment + day_variation + noise
        score = max(-1.0, min(1.0, score))
        
        classification = "Neutral"
        if score > 0.3:
            classification = "Greed"
        elif score > 0.1:
            classification = "Neutral"
        elif score > -0.1:
            classification = "Neutral"
        elif score > -0.3:
            classification = "Fear"
        else:
            classification = "Extreme Fear"
        
        return {
            'sentiment_score': round(score, 3),
            'value': int((score + 1) * 50),
            'classification': classification,
            'timestamp': datetime.now().isoformat(),
            'source': 'mock_generator'
        }
    
    async def get_fear_greed_index(self) -> Dict[str, Any]:
        """Fetch Fear & Greed Index from alternative.me"""
        try:
            import httpx
            url = "https://api.alternative.me/fng/"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                # API returns data directly without 'status' field
                if data.get('data') and len(data['data']) > 0:
                    fng_data = data['data'][0]
                    current_value = int(fng_data['value'])
                    previous_value = int(fng_data.get('previous_value', 0))
                    return {
                        'value': current_value,
                        'classification': fng_data['value_classification'],
                        'timestamp': fng_data['timestamp'],
                        'previous_value': previous_value,
                        'change': current_value - previous_value
                    }
        except Exception as e:
            self.logger.error(f"Failed to fetch F&G Index: {e}")
            return {'value': 50, 'classification': 'Neutral', 'error': str(e)}
        
        # Fallback if no data
        return {'value': 50, 'classification': 'Neutral', 'error': 'No data available'}
    
    async def _analyze_sentiment(self, text: str) -> float:
        """
        Internal method to analyze sentiment of text using NLP model
        
        Args:
            text: Text to analyze
            
        Returns:
            float: Sentiment score between -1 and 1
        """
        if not text:
            return 0.0
            
        return self.nlp_analyzer.analyze(text)


# For backward compatibility
async def get_sentiment_score(text: str) -> float:
    """
    Convenience function to get sentiment score for a single text
    """
    agent = SentimentAgent()
    return await agent.analyze(text)