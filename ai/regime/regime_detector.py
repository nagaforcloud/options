"""
AI Regime Detector for Options Wheel Strategy Trading Bot
Detects market regimes using indicators and adjusts strategy accordingly
"""
from typing import Dict, Any, Optional, Tuple
import json
from datetime import datetime

import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logging_utils import logger
from ai.base import is_enabled, call_llm
from config.config import config
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.config import config


def predict(market_snapshot: Dict[str, Any]) -> Tuple[str, float, str]:
    """
    Predict the current market regime based on market snapshot
    
    Args:
        market_snapshot: Current market conditions including NIFTY, VIX, USD-INR, news sentiment
        
    Returns:
        Tuple of (regime, confidence, explanation)
    """
    if not is_enabled("regime"):
        logger.debug("[AI] Regime detection is disabled")
        return "neutral", 0.5, "Regime detection disabled"
    
    try:
        logger.info("[AI] Regime: Predicting current market regime")
        
        # Extract relevant features from market snapshot
        nifty_data = market_snapshot.get('nifty', {})
        vix_data = market_snapshot.get('vix', {})
        news_sentiment = market_snapshot.get('news_sentiment', 0)
        
        # Create prompt for LLM regime detection
        prompt = f"""
        You are a market regime detector for the Options Wheel Strategy Trading Bot.
        
        Current Market Snapshot:
        NIFTY: {nifty_data}
        VIX: {vix_data}
        News Sentiment: {news_sentiment}
        
        Based on the provided market data, classify the current market into one of these regimes:
        - low_vol_trend: Low volatility trending market
        - high_vol_range: High volatility range-bound market
        - event_driven: Market driven by specific events
        - crash: Market crash or sharp decline
        - rally: Strong bullish market rally
        
        Consider:
        - VIX levels (>25 = high vol, <15 = low vol)
        - NIFTY trend strength and direction
        - News sentiment extremes
        - Recent price action patterns
        
        Respond ONLY in this JSON format:
        {{"regime": "regime_name", "confidence": 0.0-1.0, "explanation": "brief explanation"}}
        """
        
        # Call LLM for regime prediction
        response = call_llm(prompt, max_tokens=200)
        
        # Parse response
        try:
            result = json.loads(response)
            regime = result.get('regime', 'neutral')
            confidence = result.get('confidence', 0.5)
            explanation = result.get('explanation', 'LLM response parsing failed')
        except json.JSONDecodeError:
            # Fallback to heuristic-based approach
            regime, confidence, explanation = _detect_regime_heuristic(
                nifty_data, vix_data, news_sentiment
            )
        
        logger.info(f"[AI] Regime: Predicted regime '{regime}' with confidence {confidence:.2f}")
        return regime, confidence, explanation
        
    except Exception as e:
        logger.error(f"[AI] Regime: Error predicting regime: {e}")
        # Return neutral regime on error
        return "neutral", 0.3, f"Error: {str(e)}"


def _detect_regime_heuristic(nifty_data: Dict, vix_data: Dict, news_sentiment: float) -> Tuple[str, float, str]:
    """
    Heuristic-based regime detection when LLM fails
    
    Returns:
        Tuple of (regime, confidence, explanation)
    """
    try:
        # Extract key metrics
        vix_current = vix_data.get('current', 15)
        nifty_trend = nifty_data.get('trend', 0)
        volatility = nifty_data.get('volatility', 0.015)
        
        # Regime classification logic
        if vix_current > 25:
            if abs(nifty_trend) > 0.02:  # Strong trend
                regime = "high_vol_range"
                explanation = "High volatility with strong trend"
            else:  # Range-bound
                regime = "high_vol_range"
                explanation = "High volatility, range-bound market"
        elif vix_current < 15:
            if abs(nifty_trend) > 0.01:  # Clear trend
                regime = "low_vol_trend"
                explanation = "Low volatility trending market"
            else:
                regime = "low_vol_trend"
                explanation = "Low volatility, consolidating"
        elif abs(news_sentiment) > 0.5:
            regime = "event_driven"
            explanation = "Event-driven market based on sentiment"
        elif nifty_trend > 0.03:  # Strong positive trend
            regime = "rally"
            explanation = "Strong bullish market rally"
        elif nifty_trend < -0.03:  # Strong negative trend
            regime = "crash"
            explanation = "Market crash or sharp decline"
        else:
            regime = "neutral"
            explanation = "Neutral market conditions"
        
        # Confidence based on signal strength
        confidence = min(0.8, abs(nifty_trend) * 20 + abs(vix_current - 20) / 20)
        
        return regime, confidence, explanation
        
    except Exception as e:
        logger.warning(f"[AI] Regime: Error in heuristic detection: {e}")
        return "neutral", 0.3, f"Heuristic detection failed: {str(e)}"


def map_regime_to_mode(regime: str) -> str:
    """
    Map detected regime to strategy mode
    
    Args:
        regime: Detected market regime
        
    Returns:
        Strategy mode (conservative, balanced, aggressive)
    """
    regime_to_mode = {
        'low_vol_trend': 'aggressive',      # Trend following, can take more risk
        'high_vol_range': 'conservative',   # High volatility, reduce risk
        'event_driven': 'conservative',     # Uncertainty, play safe
        'crash': 'conservative',            # Market stress, minimal risk
        'rally': 'balanced'                 # General optimistic, balanced approach
    }
    
    mode = regime_to_mode.get(regime, config.strategy_mode)
    logger.info(f"[AI] Regime: Mapped regime '{regime}' to strategy mode '{mode}'")
    
    return mode


def get_market_regime_features(market_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract features used for regime detection from market snapshot
    
    Args:
        market_snapshot: Current market conditions
        
    Returns:
        Dictionary of features used for regime detection
    """
    features = {
        'vix_level': market_snapshot.get('vix', {}).get('current', 15),
        'vix_trend': market_snapshot.get('vix', {}).get('trend', 0),
        'nifty_trend': market_snapshot.get('nifty', {}).get('trend', 0),
        'volatility_regime': market_snapshot.get('volatility_regime', 'normal'),
        'correlation_regime': market_snapshot.get('correlation_regime', 'normal'),
        'liquidity_regime': market_snapshot.get('liquidity_regime', 'normal'),
        'news_sentiment': market_snapshot.get('news_sentiment', 0),
        'economic_data_surprise': market_snapshot.get('economic_data_surprise', 0)
    }
    
    return features


def update_regime_model(new_data: Dict[str, Any]) -> bool:
    """
    Update the regime detection model with new data
    
    Args:
        new_data: New market data for model updates
        
    Returns:
        True if update successful, False otherwise
    """
    try:
        # In a real implementation, this would update the ML model
        # For now, just log the attempt
        logger.info("[AI] Regime: Model update triggered with new data")
        return True
    except Exception as e:
        logger.error(f"[AI] Regime: Error updating model: {e}")
        return False