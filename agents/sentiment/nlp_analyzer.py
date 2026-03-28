"""
NLP Sentiment Analyzer using Hugging Face transformers
Uses the cardiffnlp/twitter-roberta-base-sentiment-latest model
"""

import logging
import os
from typing import Optional, Tuple
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Set up logging
logger = logging.getLogger(__name__)

class NLPSentimentAnalyzer:
    """
    NLP Sentiment Analyzer using Hugging Face transformers.
    Uses the cardiffnlp/twitter-roberta-base-sentiment-latest model.
    Returns sentiment scores normalized to -1.0 (very negative) to 1.0 (very positive).
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the NLP sentiment analyzer.
        
        Args:
            cache_dir: Directory to cache the model and tokenizer locally.
                      If None, uses default Hugging Face cache directory.
        """
        self.model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        self.cache_dir = cache_dir or os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "transformers")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        try:
            self._load_model()
        except Exception as e:
            logger.error(f"Failed to load NLP model: {e}")
            logger.info("Falling back to mock sentiment analysis")
            self.model = None
            self.tokenizer = None
    
    def _load_model(self):
        """Load the tokenizer and model from Hugging Face."""
        logger.info(f"Loading NLP model '{self.model_name}'...")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir,
            local_files_only=False
        )
        
        # Load model
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir,
            local_files_only=False
        )
        
        # Move model to device
        self.model.to(self.device)
        self.model.eval()
        
        logger.info(f"NLP model loaded successfully on {self.device}")
    
    def analyze(self, text: str) -> float:
        """
        Analyze sentiment of given text and return score between -1.0 and 1.0.
        
        Args:
            text: Text to analyze
            
        Returns:
            float: Sentiment score between -1.0 (very negative) and 1.0 (very positive)
                   Returns 0.0 if model is not available
        """
        if self.model is None or self.tokenizer is None:
            # Fallback to simple keyword-based analysis if model failed to load
            return self._fallback_analyze(text)
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512
            )
            
            # Move inputs to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
            
            # Convert logits to probabilities
            probabilities = torch.softmax(logits, dim=-1).cpu().numpy()[0]
            
            # The model has 3 labels: negative (0), neutral (1), positive (2)
            # Map to -1.0 to 1.0 scale: negative=-1.0, neutral=0.0, positive=1.0
            negative_prob = probabilities[0]
            neutral_prob = probabilities[1]
            positive_prob = probabilities[2]
            
            # Calculate weighted score
            score = (-1.0 * negative_prob) + (0.0 * neutral_prob) + (1.0 * positive_prob)
            
            # Ensure score is within [-1.0, 1.0]
            score = max(-1.0, min(1.0, score))
            
            return float(score)
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return self._fallback_analyze(text)
    
    def _fallback_analyze(self, text: str) -> float:
        """
        Fallback sentiment analysis using simple keyword matching.
        Used when the NLP model is not available or fails.
        
        Args:
            text: Text to analyze
            
        Returns:
            float: Sentiment score between -1.0 and 1.0
        """
        if not text:
            return 0.0
            
        text_lower = text.lower()
        
        # Define basic positive and negative words
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
            
        # Calculate sentiment ratio
        if pos_count == 0 and neg_count == 0:
            return 0.0
        
        sentiment_ratio = (pos_count - neg_count) / max(pos_count + neg_count, 1)
        
        # Apply intensity based on the number of sentiment words
        intensity_factor = min((pos_count + neg_count) / 10.0, 1.0)
        
        # Base score with intensity
        base_score = sentiment_ratio * min(intensity_factor * 2.0, 1.0)
        
        return max(-1.0, min(1.0, base_score))