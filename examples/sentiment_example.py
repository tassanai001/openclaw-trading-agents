"""
Example usage of the Sentiment Agent
"""

import asyncio
from agents.sentiment.sentiment import SentimentAgent


async def main():
    # Create sentiment agent
    agent = SentimentAgent()
    
    # Example 1: Analyze simple text
    text = "The market is showing incredible growth with strong bullish trends!"
    score = await agent.analyze(text)
    print(f"Text: {text}")
    print(f"Sentiment Score: {score}\n")
    
    # Example 2: Analyze Twitter data
    tweets = [
        "Amazing rally today! Bitcoin up 10%",
        "Concerned about inflation data coming tomorrow",
        "Tech stocks looking very strong this quarter"
    ]
    
    twitter_result = await agent.analyze_twitter_sentiment(tweets)
    print(f"Twitter Sentiment Score: {twitter_result['sentiment_score']:.3f}")
    print(f"Analyzed {twitter_result['total_tweets']} tweets\n")
    
    # Example 3: Analyze News data
    news_articles = [
        {
            'title': 'Federal Reserve Signals Rate Cut',
            'content': 'Positive implications for stock market and economic growth'
        },
        {
            'title': 'Oil Prices Surge Unexpectedly',
            'content': 'May impact inflation and consumer spending negatively'
        }
    ]
    
    news_result = await agent.analyze_news_sentiment(news_articles)
    print(f"News Sentiment Score: {news_result['sentiment_score']:.3f}")
    print(f"Analyzed {news_result['total_articles']} articles\n")
    
    # Example 4: Get overall sentiment combining both sources
    overall_result = await agent.get_overall_sentiment(
        twitter_data=tweets,
        news_data=news_articles
    )
    
    print("Overall Sentiment Analysis:")
    print(f"Combined Score: {overall_result['combined']['sentiment_score']:.3f}")
    print(f"Sources used: {overall_result['combined']['sources_used']}")
    

if __name__ == "__main__":
    asyncio.run(main())