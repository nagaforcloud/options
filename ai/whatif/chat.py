"""
Simple What-If Chat Module for Testing
"""
from typing import Dict, Any, Optional
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logging_utils import logger
from ai.base import is_enabled, call_llm
from config.config import config


def ask_what_if_question(
    question: str, 
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Ask a "what-if" scenario question using LLM
    
    Args:
        question: What-if question to ask
        context: Additional context (market data, position info, etc.)
        
    Returns:
        Answer to the what-if question
    """
    if not is_enabled("whatif"):
        logger.debug("[AI] What-if scenario chat is disabled")
        return "What-if scenario chat is disabled"
    
    try:
        logger.info(f"[AI] What-If: Processing question: {question[:50]}...")
        return f"Simulated response to: {question}"
        
    except Exception as e:
        logger.error(f"[AI] What-If: Error processing question: {e}")
        return f"Error processing your question: {str(e)}"


def get_what_if_chat_status() -> Dict[str, Any]:
    """
    Get current status of what-if scenario chat
    
    Returns:
        Dictionary with system status
    """
    return {
        "feature_enabled": is_enabled("whatif"),
        "system_health": "operational",
        "version": "1.0"
    }