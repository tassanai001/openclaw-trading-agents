"""
Sentiment Analysis Agent
Analyzes Twitter and News sentiment, returns score between -1 and 1
"""

import asyncio
import random
import logging
import numpy as np
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from .config import SentimentConfig


class SentimentAgent:
    """
    Agent that analyzes Twitter and News sentiment to return a score between -1 and 1
    """
    
    def __init__(self, config: Optional[SentimentConfig] = None):
        self.config = config or SentimentConfig()
        self._twitter_sources = []
        self._news_sources = []
        self.logger = logging.getLogger(__name__)
        
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
    
    async def get_overall_sentiment(self, twitter_data: Optional[List[str]] = None, 
                                  news_data: Optional[List[Dict]] = None,
                                  include_fng: bool = True) -> Dict:
        """
        Get overall sentiment combining Twitter, News, and Fear & Greed Index
        
        Args:
            twitter_data: List of tweets
            news_data: List of news articles
            include_fng: Whether to include Fear & Greed Index
            
        Returns:
            Dict: Combined sentiment analysis
        """
        results = {}
        
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
            
        if not has_social_data and not has_fng:
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
        Internal method to analyze sentiment of text (mock implementation)
        
        Args:
            text: Text to analyze
            
        Returns:
            float: Sentiment score between -1 and 1
        """
        # In a real implementation, this would use an NLP model or API
        # For now, we'll simulate with a more sophisticated mock
        
        # Convert to lowercase for processing
        text_lower = text.lower()
        
        # Define some basic positive and negative words
        positive_words = [
            'good', 'great', 'excellent', 'positive', 'amazing', 'wonderful',
            'fantastic', 'incredible', 'outstanding', 'perfect', 'brilliant',
            'profit', 'gains', 'bullish', 'up', 'rise', 'success', 'strong',
            'buy', 'optimistic', 'hopeful', 'beneficial', 'advantageous'
        ]
        
        negative_words = [
            'bad', 'terrible', 'awful', 'negative', 'horrible', 'disappointing',
            'poor', 'worst', 'failure', 'disaster', 'crash', 'fall', 'loss',
            'sell', 'pessimistic', 'concern', 'risk', 'danger', 'decline',
            'weak', 'bearish', 'trouble', 'problem', 'issue'
        ]
        
        # Count positive and negative words
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calculate base score
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
            
        # Calculate normalized score (-1 to 1 range)
        if pos_count == 0 and neg_count == 0:
            # If no sentiment words found, return a small random value
            return round(random.uniform(-0.1, 0.1), 3)
        
        # Calculate sentiment ratio
        sentiment_ratio = (pos_count - neg_count) / max(pos_count + neg_count, 1)
        
        # Apply intensity based on the number of sentiment words
        intensity_factor = min((pos_count + neg_count) / 10.0, 1.0)
        
        # Base score with intensity
        base_score = sentiment_ratio * min(intensity_factor * 2.0, 1.0)
        
        # Add slight randomness to make it more realistic
        noise = random.uniform(-0.05, 0.05)
        final_score = base_score + noise
        
        return round(max(-1.0, min(1.0, final_score)), 3)


# For backward compatibility
async def get_sentiment_score(text: str) -> float:
    """
    Convenience function to get sentiment score for a single text
    """
    agent = SentimentAgent()
    return await agent.analyze(text)