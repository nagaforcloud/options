"""
AI Base module for Options Wheel Strategy Trading Bot
Provides AI feature flagging system and LLM client singleton
"""
import os
from typing import Optional, Dict, Any, List
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config import config
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logging_utils import logger
import threading


class AIBase:
    """Base class for AI features with feature flagging system"""
    
    def __init__(self):
        """Initialize AI base with configuration and LLM client"""
        self.enabled_features = set(config.ai_features) if config.enable_ai_features else set()
        self.llm_client = None
        self._llm_client_lock = threading.Lock()  # For thread-safe LLM client initialization
        
        logger.info(f"AI Base initialized with features: {self.enabled_features}")
    
    def is_enabled(self, feature_flag: str) -> bool:
        """
        Check if a specific AI feature is enabled
        
        Args:
            feature_flag: Name of the AI feature to check
            
        Returns:
            True if feature is enabled, False otherwise
        """
        is_enabled = config.enable_ai_features and feature_flag in self.enabled_features
        if is_enabled:
            logger.debug(f"[AI] Feature '{feature_flag}' is enabled")
        else:
            logger.debug(f"[AI] Feature '{feature_flag}' is disabled")
        
        return is_enabled
    
    def get_llm_client(self):
        """
        Get LLM client instance (singleton pattern)
        
        Returns:
            LLM client instance
        """
        if not self.llm_client:
            with self._llm_client_lock:
                if not self.llm_client:
                    self._initialize_llm_client()
        
        return self.llm_client
    
    def _initialize_llm_client(self):
        """Initialize the LLM client based on configuration"""
        try:
            # Try to import and initialize the appropriate LLM client
            # First, check if OpenAI API key is available
            if config.openai_api_key:
                logger.info("[AI] Initializing OpenAI client")
                import openai
                openai.api_key = config.openai_api_key
                self.llm_client = openai
            else:
                # Use local LLM via Ollama if available
                logger.info("[AI] Initializing local LLM client (Ollama)")
                import ollama
                self.llm_client = ollama
            
            logger.info("[AI] LLM client initialized successfully")
        except ImportError as e:
            logger.warning(f"[AI] LLM client initialization failed due to missing dependencies: {e}")
            logger.info("[AI] Using mock LLM responses")
            self.llm_client = MockLLMClient()
        except Exception as e:
            logger.error(f"[AI] Error initializing LLM client: {e}")
            logger.info("[AI] Using mock LLM responses")
            self.llm_client = MockLLMClient()
    
    def call_llm(
        self, 
        prompt: str, 
        model: Optional[str] = None, 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Call the LLM with the given parameters
        
        Args:
            prompt: Input prompt for the LLM
            model: Model to use (defaults to config)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            LLM response as string
        """
        try:
            llm_client = self.get_llm_client()
            
            # Use default values from config if not provided
            model = model or config.ai_llm_model
            max_tokens = max_tokens or 500
            temperature = temperature or 0.7
            
            # Prepare the call based on the client type
            if hasattr(llm_client, 'ChatCompletion'):  # OpenAI
                response = llm_client.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                return response.choices[0].message.content
            elif hasattr(llm_client, 'generate'):  # Ollama
                response = llm_client.generate(
                    model=model,
                    prompt=prompt,
                    options={
                        "num_predict": max_tokens,
                        "temperature": temperature
                    },
                    **kwargs
                )
                return response['response']
            else:
                # Mock client fallback
                logger.warning("[AI] Using mock LLM response")
                return self.mock_llm_response(prompt)
        
        except Exception as e:
            logger.error(f"[AI] Error calling LLM: {e}")
            return self.mock_llm_response(prompt)
    
    def mock_llm_response(self, prompt: str) -> str:
        """
        Provide a mock LLM response for testing or when LLM is unavailable
        
        Args:
            prompt: Input prompt
            
        Returns:
            Mock response string
        """
        logger.debug(f"[AI] Mock response for prompt: {prompt[:50]}...")
        return f"[MOCK] This is a simulated response for: {prompt[:100]}..."


# Global AI base instance
ai_base = AIBase()


def is_enabled(feature_flag: str) -> bool:
    """Check if a specific AI feature is enabled"""
    return ai_base.is_enabled(feature_flag)


def call_llm(
    prompt: str, 
    model: Optional[str] = None, 
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    **kwargs
) -> str:
    """Call the LLM with the given parameters"""
    return ai_base.call_llm(prompt, model, max_tokens, temperature, **kwargs)


def get_llm_client():
    """Get the LLM client instance"""
    return ai_base.get_llm_client()


# Mock LLM Client class for fallback
class MockLLMClient:
    """Mock LLM client for testing and fallback scenarios"""
    
    def __init__(self):
        """Initialize mock client"""
        self.name = "MockLLMClient"
    
    def generate(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Mock generate method"""
        return {
            "response": f"[MOCK] Generated response for prompt: {prompt[:100]}...",
            "model": model,
            "total_duration": 0,
            "load_duration": 0
        }
    
    def chat(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Mock chat method"""
        return {
            "message": {"content": f"[MOCK] Chat response for prompt: {messages[-1]['content'] if messages else 'empty'}"},
            "model": model,
            "total_duration": 0
        }


def get_available_features() -> List[str]:
    """Get list of all available AI features"""
    return [
        "rag",           # RAG Trade Diary & Chat
        "regime",        # Regime Detector
        "stress",        # Generative Stress-Test Engine
        "slippage",      # AI Slippage Predictor
        "semantic_kill", # Semantic Kill-Switch
        "news",          # News Retrieval-Augmented Filter
        "compliance",    # AI Compliance Auditor
        "i18n",          # Multilingual Alerting
        "voice",         # Voice / WhatsApp Interface
        "synth_chain",   # Synthetic Option-Chain Imputation
        "explain",       # Explainable Greeks
        "hedge",         # Auto-Hedge Suggester
        "mapper",        # Smart CSV Column Mapper
        "whatif",        # "What-If" Scenario Chat
        "automl",        # Continuous Learning Loop
        "testgen",       # LLM Unit-Test Generator
        "kelly",         # AI-Derived Kelly Position Size
        "sentiment_kill", # Sentiment Kill-Switch
        "patch",         # AI Code-Patch Suggester
        "cache"          # Memory-Efficient Embedding Cache
    ]


def validate_feature_flags(feature_flags: List[str]) -> List[str]:
    """Validate provided feature flags against available features"""
    available = set(get_available_features())
    validated = []
    
    for flag in feature_flags:
        if flag in available:
            validated.append(flag)
        else:
            logger.warning(f"[AI] Unknown feature flag: {flag}")
    
    return validated