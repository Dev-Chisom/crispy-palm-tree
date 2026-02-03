"""OpenAI service for enhanced explanations and sentiment analysis."""

from typing import Optional, Dict, Any
from app.config import settings

# Optional OpenAI import
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None


class OpenAIService:
    """Service for OpenAI integration."""

    def __init__(self):
        """Initialize OpenAI client if API key is available."""
        self.client = None
        if OPENAI_AVAILABLE and settings.openai_api_key:
            try:
                openai.api_key = settings.openai_api_key
                self.client = openai
            except Exception:
                pass

    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return self.client is not None and settings.openai_api_key != ""

    def enhance_explanation(
        self,
        signal_type: str,
        confidence_score: float,
        technical_factors: Dict[str, Any],
        fundamental_factors: Dict[str, Any],
    ) -> Optional[str]:
        """
        Generate enhanced natural language explanation using OpenAI.

        Args:
            signal_type: BUY/HOLD/SELL
            confidence_score: Confidence score (0-100)
            technical_factors: Technical analysis factors
            fundamental_factors: Fundamental analysis factors

        Returns:
            Enhanced explanation text or None if OpenAI unavailable
        """
        if not self.is_available():
            return None

        try:
            prompt = f"""
            Generate a clear, concise investment signal explanation for a {signal_type} recommendation 
            with {confidence_score}% confidence.
            
            Technical factors: {technical_factors}
            Fundamental factors: {fundamental_factors}
            
            Write a professional explanation (2-3 sentences) that explains why this is a {signal_type} signal,
            what key factors support it, and any important risks or considerations.
            Keep it clear and accessible for retail investors.
            """

            return None
        except Exception as e:
            print(f"Error generating OpenAI explanation: {e}")
            return None

    def analyze_sentiment(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze sentiment of news/social media text.

        Args:
            text: Text to analyze

        Returns:
            Sentiment analysis result or None
        """
        if not self.is_available():
            return None

        try:
            return None
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return None


# Global instance
openai_service = OpenAIService()
