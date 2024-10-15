from .base_annotation import BaseAnnotation
from textblob import TextBlob

class SentimentAnnotation(BaseAnnotation):
    def annotate(self, text: str):
        """Sentiment analysis logic"""
        return self.analyze_sentiment(text)

    def analyze_sentiment(self, text: str):
        """Analyze the sentiment of the given text and return sentiment label and score."""
        blob = TextBlob(text)
        sentiment = "positive" if blob.sentiment.polarity > 0 else "negative" if blob.sentiment.polarity < 0 else "neutral"
        return {
            "sentiment": sentiment,
            "score": blob.sentiment.polarity  # Score ranges from -1 to 1
        }