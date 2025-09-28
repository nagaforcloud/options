"""
Semantic Kill-Switch for Options Wheel Strategy Trading Bot
LLM judges Telegram messages for kill intent with confidence threshold
"""
from typing import Dict, Any, Tuple, Optional
import re
from datetime import datetime

import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logging_utils import logger
from ai.base import is_enabled, call_llm
from config.config import config


def judge_message(message_text: str, user_id: Optional[str] = None, message_context: Optional[Dict[str, Any]] = None) -> Tuple[bool, float, str]:
    """
    Judge a Telegram message for kill-switch activation intent
    
    Args:
        message_text: Text content of the Telegram message
        user_id: ID of the user who sent the message (optional)
        message_context: Additional context about the message (optional)
        
    Returns:
        Tuple of (should_activate_kill_switch, confidence, explanation)
    """
    if not is_enabled("semantic_kill"):
        logger.debug("[AI] Semantic kill-switch is disabled")
        return False, 0.0, "Feature disabled"
    
    try:
        logger.info(f"[AI] Semantic Kill: Judging message: {message_text[:50]}...")
        
        # First, check for obvious kill commands using regex
        has_obvious_kill_intent, regex_confidence = _check_obvious_kill_intent(message_text)
        if has_obvious_kill_intent and regex_confidence >= 0.95:
            logger.info(f"[AI] Semantic Kill: Obvious kill intent detected with {regex_confidence:.2f} confidence")
            return True, regex_confidence, "Obvious kill command detected"
        
        # Use LLM for nuanced judgment
        prompt = f"""
        You are a risk management AI assistant for the Options Wheel Strategy Trading Bot.
        
        Your task is to judge Telegram messages for kill-switch activation intent.
        
        Message to analyze: "{message_text}"
        
        User ID: {user_id or "Unknown"}
        Message Context: {message_context or "No additional context"}
        
        Analyze the message and determine if the user wants to:
        1. Emergency stop trading (KILL)
        2. Pause the bot temporarily (PAUSE)  
        3. Request clarification (INQUIRE)
        4. No action needed (OK)
        
        Decision criteria:
        - KILL: Immediate emergency stop (confidence > 0.9)
        - PAUSE: Temporary pause (confidence > 0.8)
        - INQUIRE: Request clarification (confidence 0.5-0.8)
        - OK: No action needed (confidence < 0.5)
        
        Keywords indicating kill intent:
        - STOP, HALT, EMERGENCY, KILL, SHUTDOWN, PAUSE, SUSPEND, DISABLE
        - CRASH, DISASTER, LOSS, DRAWDOWN, BROKEN
        
        Consider:
        - Message urgency and tone
        - Crisis terminology and emotional language
        - Explicit commands vs. questions
        - User authority level (if known)
        - Context clues from previous messages
        
        Respond ONLY in this JSON format:
        {{"decision": "KILL"|"PAUSE"|"INQUIRE"|"OK", "confidence": 0.0-1.0, "explanation": "brief explanation"}}
        """
        
        # Call LLM for judgment
        response = call_llm(prompt, max_tokens=150, temperature=0.3)  # Low temperature for consistent responses
        
        # Parse LLM response
        try:
            import json
            result = json.loads(response)
            decision = result.get('decision', 'OK')
            confidence = float(result.get('confidence', 0.0))
            explanation = result.get('explanation', 'No explanation provided')
        except (json.JSONDecodeError, ValueError, KeyError):
            # Fallback to heuristic judgment
            decision, confidence, explanation = _heuristic_judgment(message_text)
        
        # Convert decision to boolean for kill switch activation
        should_activate = decision in ['KILL', 'PAUSE']
        
        # Apply confidence threshold
        if confidence < config.semantic_kill_confidence_threshold:
            should_activate = False
            confidence *= 0.5  # Reduce confidence for low-threshold decisions
            explanation += f" (Confidence below threshold {config.semantic_kill_confidence_threshold})"
        
        logger.info(f"[AI] Semantic Kill: Decision={decision}, Activate={should_activate}, Confidence={confidence:.2f}")
        return should_activate, confidence, explanation
        
    except Exception as e:
        logger.error(f"[AI] Semantic Kill: Error judging message: {e}")
        # Conservative fallback - don't activate kill switch on error
        return False, 0.1, f"Error in judgment: {str(e)}"


def _check_obvious_kill_intent(message_text: str) -> Tuple[bool, float]:
    """
    Check for obvious kill intent using regex patterns
    
    Args:
        message_text: Text content of the message
        
    Returns:
        Tuple of (has_kill_intent, confidence)
    """
    # Convert to lowercase for case-insensitive matching
    text_lower = message_text.lower().strip()
    
    # High-confidence kill keywords
    high_confidence_patterns = [
        r'\b(stop|halt|emergency|kill|shutdown|terminate)\b',
        r'\b(immediate|urgent|now|asap)\s+(stop|halt|kill|shutdown)\b',
        r'^(stop|halt|kill|shutdown)\s*(now|immediately|right\s*away)?\s*$',
        r'\b(emergency\s+stop|kill\s+switch|emergency\s+kill)\b'
    ]
    
    # Medium-confidence patterns
    medium_confidence_patterns = [
        r'\b(pause|suspend|disable)\b',
        r'\b(problem|issue|broken|not\s+working)\b',
        r'\b(loss(es)?|drawdown|crash|disaster)\b',
        r'\b(help|assistance|required)\s+(stop|halt|pause)\b'
    ]
    
    # Check for high-confidence patterns
    for pattern in high_confidence_patterns:
        if re.search(pattern, text_lower):
            return True, 0.95
    
    # Check for medium-confidence patterns
    for pattern in medium_confidence_patterns:
        if re.search(pattern, text_lower):
            return True, 0.75
    
    # No obvious kill intent detected
    return False, 0.1


def _heuristic_judgment(message_text: str) -> Tuple[str, float, str]:
    """
    Heuristic-based judgment when LLM fails
    
    Args:
        message_text: Text content of the message
        
    Returns:
        Tuple of (decision, confidence, explanation)
    """
    text_lower = message_text.lower().strip()
    
    # Crisis/emergency keywords with high weight
    crisis_keywords = [
        'emergency', 'crisis', 'disaster', 'panic', 'catastrophe', 
        'critical', 'urgent', 'immediate', 'asap', 'now'
    ]
    
    # Stop/kill keywords with medium weight
    stop_keywords = [
        'stop', 'halt', 'kill', 'shutdown', 'terminate', 'cancel',
        'pause', 'suspend', 'disable', 'freeze'
    ]
    
    # Problem/concern keywords with low weight
    concern_keywords = [
        'problem', 'issue', 'broken', 'not working', 'error',
        'loss', 'drawdown', 'crash', 'down'
    ]
    
    # Calculate keyword scores
    crisis_score = sum(1 for keyword in crisis_keywords if keyword in text_lower)
    stop_score = sum(1 for keyword in stop_keywords if keyword in text_lower)
    concern_score = sum(1 for keyword in concern_keywords if keyword in text_lower)
    
    # Calculate total score
    total_score = (crisis_score * 3) + (stop_score * 2) + concern_score
    
    # Determine decision based on score
    if total_score >= 5:  # High confidence crisis situation
        return "KILL", 0.9, f"High crisis score: {total_score}"
    elif total_score >= 3:  # Medium confidence stop request
        return "PAUSE", 0.7, f"Medium stop score: {total_score}"
    elif total_score >= 1:  # Low confidence concern
        return "INQUIRE", 0.4, f"Low concern score: {total_score}"
    else:  # No clear intent
        return "OK", 0.2, f"No clear intent detected, score: {total_score}"


def should_respond_to_user(user_id: Optional[str] = None, user_role: Optional[str] = None) -> bool:
    """
    Determine if the bot should respond to a specific user
    
    Args:
        user_id: ID of the user (optional)
        user_role: Role of the user (admin, user, guest, etc.)
        
    Returns:
        True if bot should respond, False otherwise
    """
    # Always respond to admins
    if user_role and user_role.lower() == 'admin':
        return True
    
    # Respond to known users
    if user_id:
        # In a real implementation, you'd check against a user database
        # For now, assume all users in a whitelist can trigger kill switch
        authorized_users = config.telegram_chat_id.split(',') if config.telegram_chat_id else []
        return user_id in authorized_users
    
    # Default: Don't respond to unknown users for safety
    return False


def generate_kill_confirmation_prompt(message_text: str) -> str:
    """
    Generate a confirmation prompt for kill switch activation
    
    Args:
        message_text: Original message that triggered kill consideration
        
    Returns:
        Confirmation prompt for user
    """
    return f"""
    🔴 KILL SWITCH ACTIVATION REQUESTED 🔴
    
    Message: "{message_text}"
    
    Are you sure you want to activate the kill switch?
    This will immediately halt all trading activities.
    
    Type "CONFIRM KILL" to proceed or "CANCEL" to abort.
    
    ⚠️ ACTION REQUIRED WITHIN 60 SECONDS ⚠️
    """


def log_kill_switch_event(
    message_text: str, 
    user_id: Optional[str], 
    decision: str, 
    confidence: float, 
    explanation: str,
    action_taken: bool
) -> None:
    """
    Log kill switch judgment event
    
    Args:
        message_text: Text of the analyzed message
        user_id: ID of the user who sent the message
        decision: Decision made (KILL, PAUSE, INQUIRE, OK)
        confidence: Confidence level in the decision
        explanation: Explanation for the decision
        action_taken: Whether any action was taken based on the decision
    """
    try:
        event_log = {
            "timestamp": datetime.now().isoformat(),
            "message_preview": message_text[:100] + ("..." if len(message_text) > 100 else ""),
            "user_id": user_id,
            "decision": decision,
            "confidence": confidence,
            "explanation": explanation,
            "action_taken": action_taken
        }
        
        logger.info(f"[AI] Semantic Kill: Event logged - {decision} ({confidence:.2f}) - Action: {action_taken}")
        
        # In a real implementation, you might want to:
        # 1. Store in a database for audit trail
        # 2. Send notification to admin channel
        # 3. Trigger additional security checks
        
    except Exception as e:
        logger.error(f"[AI] Semantic Kill: Error logging event: {e}")


def validate_kill_switch_request(message_text: str, user_id: Optional[str]) -> Tuple[bool, str]:
    """
    Validate a potential kill switch request
    
    Args:
        message_text: Text of the message
        user_id: ID of the user who sent the message
        
    Returns:
        Tuple of (is_valid_request, validation_message)
    """
    try:
        # Check if user is authorized
        if not should_respond_to_user(user_id):
            return False, "Unauthorized user - kill switch request denied"
        
        # Check if message contains any stop-related keywords
        text_lower = message_text.lower()
        stop_keywords = ['stop', 'kill', 'halt', 'shutdown', 'emergency', 'pause']
        
        has_stop_keyword = any(keyword in text_lower for keyword in stop_keywords)
        if not has_stop_keyword:
            return False, "Message does not contain recognized stop keywords"
        
        # Additional validation could include:
        # 1. Rate limiting (prevent spam)
        # 2. Time-based restrictions
        # 3. Context validation
        # 4. Multi-factor authentication
        
        return True, "Valid kill switch request"
        
    except Exception as e:
        logger.error(f"[AI] Semantic Kill: Error validating request: {e}")
        return False, f"Validation error: {str(e)}"


def get_kill_switch_status() -> Dict[str, Any]:
    """
    Get current status of the semantic kill switch system
    
    Returns:
        Dictionary with system status information
    """
    return {
        "feature_enabled": is_enabled("semantic_kill"),
        "confidence_threshold": config.semantic_kill_confidence_threshold,
        "last_judgment": datetime.now().isoformat(),
        "total_judgments": 0,  # Would track actual judgments in real implementation
        "successful_activations": 0,  # Would track actual activations
        "false_positives": 0,  # Would track rejected legitimate requests
        "system_health": "operational",
        "version": "1.0"
    }