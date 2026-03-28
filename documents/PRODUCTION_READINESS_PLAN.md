# Production Readiness Plan

**Created:** 2026-03-28  
**Goal:** Convert mock-based agents to production-ready implementations with real API integrations

## Overview

This plan outlines the steps to convert 3 agents from mock/synthetic data implementations to production-ready systems with real API integrations:

1. **Scanner Agent** - Currently generates synthetic OHLCV data
2. **Sentiment Agent** - Uses mock NLP and lacks Twitter/News API integration
3. **Execution Agent** - Has mock slippage/liquidity validation

---

## Phase 1: Scanner Agent Productionization

### Current State
- **File:** `agents/scanner/scanner.py`
- **Issue:** `_fetch_market_data()` generates synthetic data using `np.random.randn()`
- **Impact:** All technical indicators (Supertrend, RSI, MACD) are calculated on fake data

### Implementation Plan

#### 1.1 Create Binance Klines API Client
**New File:** `agents/scanner/binance_klines_client.py`

```python
"""
Binance Klines (Candlestick) API Client
Fetches historical OHLCV data from Binance API
"""
```

**Requirements:**
- Use `python-binance` AsyncClient for async operations
- Support multiple timeframes: 1m, 5m, 15m, 1h, 4h, 1d
- Fetch minimum 100 candles for indicator calculations
- Handle rate limits (1200 requests/minute for most endpoints)
- Implement retry logic with exponential backoff
- Cache recent results to reduce API calls

**Functions:**
```python
async def get_klines(
    symbol: str,           # e.g., "BTCUSDT"
    interval: str,         # e.g., "5m", "1h"
    limit: int = 100,      # Number of candles
    start_time: Optional[int] = None,
    end_time: Optional[int] = None
) -> pd.DataFrame:
    """Fetch OHLCV data from Binance"""
```

**Error Handling:**
- BinanceAPIException → Log error, return cached data or None
- ConnectionError → Retry 3 times with backoff
- RateLimitError → Wait and retry

#### 1.2 Update Scanner Agent
**File:** `agents/scanner/scanner.py`

**Changes:**
1. Import new client:
   ```python
   from .binance_klines_client import BinanceKlinesClient
   ```

2. Update `__init__`:
   ```python
   self.klines_client = BinanceKlinesClient()
   self.use_real_data = True  # Configurable
   ```

3. Rewrite `_fetch_market_data()`:
   - Try real API first (Binance Klines)
   - Fall back to BinancePriceFetcher for current price + synthetic history (if real data unavailable)
   - Last resort: Full synthetic data (current implementation)

4. Add configuration option:
   ```python
   # In config.py
   USE_REAL_MARKET_DATA: bool = True  # Set False for testing
   ```

#### 1.3 Testing Strategy

**Unit Tests:**
- Test klines client with mock Binance responses
- Test scanner with both real and fallback modes
- Verify indicator calculations on real data

**Integration Tests:**
- Live test against Binance testnet
- Verify rate limiting doesn't trigger
- Check data consistency across timeframes

### Success Criteria
- [ ] Scanner can fetch real OHLCV data from Binance
- [ ] All indicators (Supertrend, RSI, MACD, MA, EMA) calculate on real data
- [ ] Fallback to synthetic data works when API unavailable
- [ ] Rate limits respected (no 429 errors)
- [ ] Unit tests pass

### Time Estimate
- Implementation: 2-3 hours
- Testing: 1-2 hours
- **Total: 4-5 hours**

---

## Phase 2: Sentiment Agent Productionization

### Current State
- **File:** `agents/sentiment/sentiment.py`
- **Issues:**
  1. `_analyze_sentiment()` uses keyword matching instead of NLP model
  2. No Twitter API integration
  3. No News API integration
  4. Falls back to `_generate_mock_sentiment()` when no data available

### Implementation Plan

#### 2.1 Integrate Real NLP Model
**Options:**
1. **Hugging Face Transformers** (Recommended)
   - Model: `cardiffnlp/twitter-roberta-base-sentiment-latest`
   - Pros: Free, crypto-trained, runs locally
   - Cons: Requires ~500MB download, CPU intensive

2. **OpenAI API**
   - Model: `gpt-3.5-turbo` or `gpt-4`
   - Pros: High accuracy, handles context well
   - Cons: Costs money, rate limits, latency

**Implementation:**
```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer

class NLPSentimentAnalyzer:
    """Real NLP sentiment analysis using RoBERTa"""
    
    def __init__(self):
        self.model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
    
    async def analyze(self, text: str) -> float:
        # Returns score -1.0 to 1.0
```

#### 2.2 Add Twitter API Integration
**New File:** `agents/sentiment/twitter_client.py`

**Requirements:**
- Use Twitter API v2 (Essential or Elevated access)
- Search recent tweets by:
  - Cashtags: `$BTC`, `$ETH`, etc.
  - Keywords: "Bitcoin", "Ethereum" + sentiment terms
- Filter: English only, no retweets, min 10 likes
- Rate limit: 450 requests/15 min (Essential)

**Functions:**
```python
async def search_tweets(
    query: str,           # e.g., "$BTC OR #Bitcoin"
    max_results: int = 100,
    start_time: Optional[datetime] = None
) -> List[str]:
    """Fetch recent tweets matching query"""
```

**Environment Variables:**
```bash
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_BEARER_TOKEN=your_bearer_token
```

#### 2.3 Add News API Integration
**New File:** `agents/sentiment/news_client.py`

**Options:**
1. **CryptoPanic API** (Recommended - crypto focused)
   - URL: `https://cryptopanic.com/api/v1/posts/`
   - Pros: Crypto-specific, includes sentiment votes
   - Cons: Requires API key

2. **NewsAPI.org**
   - URL: `https://newsapi.org/v2/everything`
   - Pros: General news, free tier
   - Cons: Not crypto-specific

3. **GNews**
   - URL: `https://gnews.io/api/v4/search`
   - Pros: Simple API
   - Cons: Limited free tier

**Implementation:**
```python
async def get_crypto_news(
    currencies: List[str],    # e.g., ["BTC", "ETH"]
    hours_back: int = 24
) -> List[Dict]:
    """Fetch recent crypto news articles"""
```

**Environment Variables:**
```bash
CRYPTOPANIC_API_KEY=your_key
# OR
NEWSAPI_KEY=your_key
```

#### 2.4 Update Sentiment Agent
**File:** `agents/sentiment/sentiment.py`

**Changes:**
1. Add new clients:
   ```python
   from .twitter_client import TwitterClient
   from .news_client import NewsClient
   from .nlp_analyzer import NLPSentimentAnalyzer
   ```

2. Update `get_overall_sentiment()`:
   - Try Twitter API first
   - Try News API second
   - Use NLP model for text analysis (not keyword matching)
   - Keep F&G Index (already working)
   - Remove mock fallback (or keep only for testing)

3. Deprecate keyword-based analysis:
   - Move `_analyze_sentiment()` to legacy mode
   - Use NLP model by default

#### 2.5 Testing Strategy

**Unit Tests:**
- Mock Twitter API responses
- Mock News API responses
- Test NLP model with sample texts
- Verify sentiment scoring accuracy

**Integration Tests:**
- Live Twitter API test (limited calls)
- Live News API test
- Compare NLP vs keyword results

### Success Criteria
- [ ] Twitter API integration fetches real tweets
- [ ] News API integration fetches real articles
- [ ] NLP model analyzes sentiment (not keyword matching)
- [ ] Combined sentiment uses real data sources
- [ ] Mock fallback removed or clearly marked for testing only
- [ ] Unit tests pass

### Time Estimate
- NLP integration: 2-3 hours
- Twitter API: 2-3 hours
- News API: 1-2 hours
- Testing: 2-3 hours
- **Total: 7-11 hours**

---

## Phase 3: Execution Agent Improvements

### Current State
- **File:** `agents/execution/execution.py`
- **Issues:**
  1. `validate_slippage()` uses mock value (0.1%)
  2. `check_liquidity()` uses mock value (100,000)
  3. Multiple placeholder prices ($50000.0)

### Implementation Plan

#### 3.1 Real Slippage Validation
**New File:** `agents/execution/slippage_validator.py`

**Implementation:**
```python
class SlippageValidator:
    """Calculate real slippage from order book"""
    
    async def get_slippage(
        self,
        symbol: str,
        side: str,        # "BUY" or "SELL"
        size: float,      # Order size
        price: float      # Expected price
    ) -> float:
        """
        Calculate expected slippage based on order book depth
        """
        # Fetch order book from exchange
        # Calculate weighted average price for order size
        # Return slippage percentage
```

**Sources:**
- Binance: `GET /api/v3/depth` (order book)
- Hyperliquid: Order book via SDK

**Calculation:**
```python
# For buy order:
# Walk up asks until size filled
# Calculate VWAP
# Slippage = (VWAP - mid_price) / mid_price * 100
```

#### 3.2 Real Liquidity Check
**New File:** `agents/execution/liquidity_checker.py`

**Implementation:**
```python
class LiquidityChecker:
    """Check available liquidity in order book"""
    
    async def check_liquidity(
        self,
        symbol: str,
        side: str,
        required_size: float
    ) -> Tuple[bool, float]:
        """
        Check if enough liquidity exists
        Returns: (is_sufficient, available_size)
        """
```

**Checks:**
- Available volume within 1% of mid-price
- Minimum $50,000 liquidity required
- Return available size for logging

#### 3.3 Update Execution Agent
**File:** `agents/execution/execution.py`

**Changes:**
1. Add validators:
   ```python
   from .slippage_validator import SlippageValidator
   from .liquidity_checker import LiquidityChecker
   ```

2. Update `validate_slippage()`:
   - Use real order book data
   - Compare against configured max slippage (0.5%)

3. Update `check_liquidity()`:
   - Use real order book depth
   - Check against configured minimum

4. Remove placeholder prices:
   - Line 105: `_calculate_paper_order_price()`
   - Line 252: `_validate_paper_order()`
   - Line 428: `get_account_info()`

#### 3.4 Testing Strategy

**Unit Tests:**
- Mock order book data
- Test slippage calculations
- Test liquidity checks

**Integration Tests:**
- Live order book fetch from Binance
- Live order book fetch from Hyperliquid
- Compare calculated vs actual slippage

### Success Criteria
- [ ] Slippage validation uses real order book data
- [ ] Liquidity check uses real order book depth
- [ ] All placeholder prices removed
- [ ] Validation prevents high-slippage trades
- [ ] Unit tests pass

### Time Estimate
- Slippage validator: 2-3 hours
- Liquidity checker: 1-2 hours
- Update execution agent: 1-2 hours
- Testing: 1-2 hours
- **Total: 5-9 hours**

---

## Environment Variables Summary

Add to `.env` file:

```bash
# Binance (for Scanner + Execution)
BINANCE_API_KEY=optional_for_public_endpoints
BINANCE_API_SECRET=optional_for_public_endpoints
BINANCE_USE_TESTNET=false

# Twitter (for Sentiment)
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# News (for Sentiment - choose one)
CRYPTOPANIC_API_KEY=your_key
# OR
NEWSAPI_KEY=your_key

# Hyperliquid (for Execution - already exists)
HYPERLIQUID_API_KEY=wallet_address
HYPERLIQUID_PRIVATE_KEY=private_key
HYPERLIQUID_IS_TESTNET=true

# Feature Flags
USE_REAL_MARKET_DATA=true
USE_REAL_SENTIMENT=true
USE_REAL_VALIDATION=true
```

---

## Implementation Order & Priorities

### Priority 1: Scanner Agent (Start Here)
**Why first?**
- Foundation for all trading decisions
- No external dependencies (Binance has public endpoints)
- Easiest to implement and test
- Immediate impact on signal quality

### Priority 2: Sentiment Agent
**Why second?**
- Requires API keys (Twitter/News)
- More complex (3 new integrations)
- Depends on Scanner for timing

### Priority 3: Execution Agent
**Why third?**
- Already functional for basic trading
- Improvements are optimizations, not blockers
- Can use paper trading while improving

---

## Testing Checklist

### Before Each Phase
- [ ] Create feature branch
- [ ] Write tests first (TDD)
- [ ] Set up environment variables

### After Each Phase
- [ ] All unit tests pass
- [ ] Integration tests pass (live APIs)
- [ ] Fallback modes tested
- [ ] Error handling verified
- [ ] Documentation updated
- [ ] PR reviewed and merged

### Final Validation
- [ ] Full trading cycle test (paper trading)
- [ ] All agents use real data
- [ ] No mock data in production paths
- [ ] Performance acceptable (< 5s per cycle)
- [ ] Error rates < 1%

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| API rate limits | High | Implement caching, backoff, request batching |
| API downtime | Medium | Keep fallback to demo mode, alert on failure |
| Twitter API costs | Low | Start with free tier, monitor usage |
| NLP model performance | Low | Use lightweight model, cache results |
| Data inconsistency | Medium | Validate data freshness, use multiple sources |

---

## Success Metrics

After all phases complete:

- Scanner: 100% real OHLCV data (no synthetic)
- Sentiment: >80% real data sources (Twitter + News + F&G)
- Execution: 100% real validation (slippage + liquidity)
- Uptime: >99% (with fallbacks)
- Latency: <3s per agent call

---

## Next Steps

1. **Review this plan** - Approve or request changes
2. **Set up API keys** - Twitter, News, Binance (if not already done)
3. **Start Phase 1** - Scanner Agent productionization
4. **Daily standups** - Review progress, blockers

---

**Ready to start?** Confirm and I'll begin Phase 1: Scanner Agent.
