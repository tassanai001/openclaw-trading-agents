# Sentiment Agent

**Generated:** 2026-03-28  
**Language:** Python 3.10+

## OVERVIEW

Market sentiment analysis combining Twitter (40%), News (60%), and Fear & Greed Index. Returns normalized score -1.0 to 1.0.

## STRUCTURE

```
agents/sentiment/
├── sentiment.py  # Main implementation
├── config.py     # SentimentConfig dataclass
└── __init__.py   # Exports SentimentAgent class
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Text analysis | `sentiment.py:analyze()` | Mock NLP with word list |
| Twitter analysis | `sentiment.py:analyze_twitter_sentiment()` | List of tweet texts |
| News analysis | `sentiment.py:analyze_news_sentiment()` | List of {title, content} |
| Combined score | `sentiment.py:get_overall_sentiment()` | Weighted average |
| F&G Index | `sentiment.py:get_fear_greed_index()` | alternative.me API |

## CONVENTIONS

- **Weights**: Twitter 40%, News 60%, F&G 40% (when included)
- **Mock fallback**: Time-based cyclical patterns when no real data
- **Signal range**: -1.0 (BEARISH) to 1.0 (BULLISH)

## ANTI-PATTERNS

- **Never** skip F&G circuit breakers — halt at < 20 or > 80
- **Never** return unweighted averages without source tracking
