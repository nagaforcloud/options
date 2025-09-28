"""
Configuration module for Options Wheel Strategy Trading Bot
Handles loading and validation of environment variables
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
from typing import List, Optional


# Load environment variables from .env file
load_dotenv()


@dataclass
class OptionWheelConfig:
    """Configuration class for the Options Wheel Strategy"""
    # API Credentials
    api_key: str = os.getenv('KITE_API_KEY', '')
    api_secret: str = os.getenv('KITE_API_SECRET', '')
    access_token: str = os.getenv('KITE_ACCESS_TOKEN', '')
    
    # Trading Parameters
    symbol: str = os.getenv('SYMBOL', 'TCS')
    quantity_per_lot: int = int(os.getenv('QUANTITY_PER_LOT', '150'))
    profit_target_percentage: float = float(os.getenv('PROFIT_TARGET_PERCENTAGE', '0.50'))
    loss_limit_percentage: float = float(os.getenv('LOSS_LIMIT_PERCENTAGE', '1.00'))
    
    # Delta Range
    otm_delta_range_low: float = float(os.getenv('OTM_DELTA_RANGE_LOW', '0.15'))
    otm_delta_range_high: float = float(os.getenv('OTM_DELTA_RANGE_HIGH', '0.25'))
    
    # Open Interest
    min_open_interest: int = int(os.getenv('MIN_OPEN_INTEREST', '1000'))
    
    # Strategy Timing
    strategy_run_interval_seconds: int = int(os.getenv('STRATEGY_RUN_INTERVAL_SECONDS', '300'))
    market_open_hour: int = int(os.getenv('MARKET_OPEN_HOUR', '9'))
    market_open_minute: int = int(os.getenv('MARKET_OPEN_MINUTE', '9'))
    market_close_hour: int = int(os.getenv('MARKET_CLOSE_HOUR', '15'))
    market_close_minute: int = int(os.getenv('MARKET_CLOSE_MINUTE', '30'))
    
    # Risk Management
    max_concurrent_positions: int = int(os.getenv('MAX_CONCURRENT_POSITIONS', '5'))
    max_daily_loss_limit: float = float(os.getenv('MAX_DAILY_LOSS_LIMIT', '5000.0'))
    max_portfolio_risk: float = float(os.getenv('MAX_PORTFOLIO_RISK', '0.02'))
    
    # Notification Settings
    enable_notifications: bool = os.getenv('ENABLE_NOTIFICATIONS', 'false').lower() == 'true'
    notification_webhook_url: str = os.getenv('NOTIFICATION_WEBHOOK_URL', '')
    notification_type: str = os.getenv('NOTIFICATION_TYPE', 'webhook')
    telegram_bot_token: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    telegram_chat_id: str = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Data Settings
    use_nse_api: bool = os.getenv('USE_NSE_API', 'true').lower() == 'true'
    data_refresh_interval: int = int(os.getenv('DATA_REFRESH_INTERVAL', '60'))
    use_nifty: bool = os.getenv('USE_NIFTY', 'false').lower() == 'true'
    
    # Enhanced Safety & Compliance Settings
    dry_run: bool = os.getenv('DRY_RUN', 'false').lower() == 'true'
    use_holiday_calendar: bool = os.getenv('USE_HOLIDAY_CALENDAR', 'false').lower() == 'true'
    holiday_file_path: str = os.getenv('HOLIDAY_FILE_PATH', './data/nse_holidays.csv')
    strategy_mode: str = os.getenv('STRATEGY_MODE', 'balanced')
    risk_per_trade_percent: float = float(os.getenv('RISK_PER_TRADE_PERCENT', '0.01'))
    min_cash_reserve: int = int(os.getenv('MIN_CASH_RESERVE', '10000'))
    enable_auto_roll: bool = os.getenv('ENABLE_AUTO_ROLL', 'false').lower() == 'true'
    kill_switch_file: str = os.getenv('KILL_SWITCH_FILE', 'STOP_TRADING')
    
    # AI & Advanced Analytics Settings
    enable_ai_features: bool = os.getenv('ENABLE_AI_FEATURES', 'false').lower() == 'true'
    ai_features: List[str] = field(default_factory=lambda: os.getenv('AI_FEATURES', 'rag,regime,slippage,news,stress,compliance').split(','))
    ai_model_dir: str = os.getenv('AI_MODEL_DIR', './data/ai_models')
    ai_rag_embedding_model: str = os.getenv('AI_RAG_EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    ai_llm_model: str = os.getenv('AI_LLM_MODEL', 'llama3:8b')
    ai_llm_base_url: str = os.getenv('AI_LLM_BASE_URL', 'http://localhost:11434')
    ai_llm_timeout: int = int(os.getenv('AI_LLM_TIMEOUT', '30'))
    ai_max_context_days: int = int(os.getenv('AI_MAX_CONTEXT_DAYS', '90'))
    ai_confidence_threshold: float = float(os.getenv('AI_CONFIDENCE_THRESHOLD', '0.7'))
    ai_decision_logging: bool = os.getenv('AI_DECISION_LOGGING', 'false').lower() == 'true'
    vector_db_path: str = os.getenv('VECTOR_DB_PATH', './ai/data/chroma.sqlite3')
    openai_api_key: str = os.getenv('OPENAI_API_KEY', '')
    rag_confidence_threshold: float = float(os.getenv('RAG_CONFIDENCE_THRESHOLD', '0.7'))
    regime_lookback_days: int = int(os.getenv('REGIME_LOOKBACK_DAYS', '30'))
    regime_confidence_threshold: float = float(os.getenv('REGIME_CONFIDENCE_THRESHOLD', '0.7'))
    slippage_bps: int = int(os.getenv('SLIPPAGE_BPS', '5'))
    slippage_model_path: str = os.getenv('SLIPPAGE_MODEL_PATH', './ai/models/slippage_model.joblib')
    slippage_scaler_path: str = os.getenv('SLIPPAGE_SCALER_PATH', './ai/models/slippage_scaler.joblib')
    stress_db_path: str = os.getenv('STRESS_DB_PATH', './ai/data/stress_results.db')
    news_vector_db_path: str = os.getenv('NEWS_VECTOR_DB_PATH', './ai/data/news_chroma.sqlite3')
    compliance_reports_dir: str = os.getenv('COMPLIANCE_REPORTS_DIR', './compliance_reports')
    alert_language: str = os.getenv('ALERT_LANGUAGE', 'en')
    twilio_account_sid: str = os.getenv('TWILIO_ACCOUNT_SID', '')
    twilio_auth_token: str = os.getenv('TWILIO_AUTH_TOKEN', '')
    twilio_phone_number: str = os.getenv('TWILIO_PHONE_NUMBER', '')
    voice_max_requests_per_hour: int = int(os.getenv('VOICE_MAX_REQUESTS_PER_HOUR', '10'))
    synth_chain_model_path: str = os.getenv('SYNTH_CHAIN_MODEL_PATH', './ai/models/synth_chain_vae.joblib')
    use_synth_chain: bool = os.getenv('USE_SYNTH_CHAIN', 'false').lower() == 'true'
    allow_synthetic_strikes: bool = os.getenv('ALLOW_SYNTHETIC_STRIKES', 'false').lower() == 'true'
    model_registry_path: str = os.getenv('MODEL_REGISTRY_PATH', './ai/models/registry.json')
    auto_ml_min_data: int = int(os.getenv('AUTO_ML_MIN_DATA', '100'))
    auto_ml_auc_threshold: float = float(os.getenv('AUTO_ML_AUC_THRESHOLD', '0.02'))
    auto_ml_check_interval_hours: int = int(os.getenv('AUTO_ML_CHECK_INTERVAL_HOURS', '24'))
    llm_tests_output_dir: str = os.getenv('LLM_TESTS_OUTPUT_DIR', './tests/llm_generated')
    kelly_fraction: float = float(os.getenv('KELLY_FRACTION', '0.5'))
    kelly_model_path: str = os.getenv('KELLY_MODEL_PATH', './ai/models/kelly_model.pth')
    sentiment_kill_threshold: float = float(os.getenv('SENTIMENT_KILL_THRESHOLD', '-0.7'))
    sentiment_volume_threshold: float = float(os.getenv('SENTIMENT_VOLUME_THRESHOLD', '2.0'))
    patch_issue_template_path: str = os.getenv('PATCH_ISSUE_TEMPLATE_PATH', './issue_template.md')
    patch_suggestions_cache_path: str = os.getenv('PATCH_SUGGESTIONS_CACHE_PATH', './ai/data/patch_suggestions.json')
    embedding_cache_size: int = int(os.getenv('EMBEDDING_CACHE_SIZE', '1000'))
    embedding_cache_ttl: int = int(os.getenv('EMBEDDING_CACHE_TTL', '3600'))
    embedding_lru_size: int = int(os.getenv('EMBEDDING_LRU_SIZE', '100'))
    use_redis_cache: bool = os.getenv('USE_REDIS_CACHE', 'false').lower() == 'true'
    redis_host: str = os.getenv('REDIS_HOST', 'localhost')
    redis_port: int = int(os.getenv('REDIS_PORT', '6379'))
    redis_db: int = int(os.getenv('REDIS_DB', '0'))
    embedding_cache_db_path: str = os.getenv('EMBEDDING_CACHE_DB_PATH', './ai/data/embedding_cache.db')
    semantic_kill_confidence_threshold: float = float(os.getenv('SEMANTIC_KILL_CONFIDENCE_THRESHOLD', '0.9'))
    csv_mapping_db_path: str = os.getenv('CSV_MAPPING_DB_PATH', './ai/data/csv_mappings.db')
    
    # Additional Settings
    include_fees_in_backtest: bool = os.getenv('INCLUDE_FEES_IN_BACKTEST', 'true').lower() == 'true'
    
    # Safety & Compliance Settings
    dry_run: bool = os.getenv('DRY_RUN', 'false').lower() == 'true'
    live_trading_confirmation_required: bool = os.getenv('LIVE_TRADING_CONFIRMATION_REQUIRED', 'true').lower() == 'true'
    kill_switch_file: str = os.getenv('KILL_SWITCH_FILE', 'STOP_TRADING')
    use_holiday_calendar: bool = os.getenv('USE_HOLIDAY_CALENDAR', 'false').lower() == 'true'
    holiday_file_path: str = os.getenv('HOLIDAY_FILE_PATH', './data/nse_holidays.csv')
    strategy_mode: str = os.getenv('STRATEGY_MODE', 'balanced')
    risk_per_trade_percent: float = float(os.getenv('RISK_PER_TRADE_PERCENT', '0.01'))
    min_cash_reserve: int = int(os.getenv('MIN_CASH_RESERVE', '10000'))
    enable_auto_roll: bool = os.getenv('ENABLE_AUTO_ROLL', 'false').lower() == 'true'
    
    # Market Data Reliability
    use_nse_api: bool = os.getenv('USE_NSE_API', 'true').lower() == 'true'
    data_refresh_interval: int = int(os.getenv('DATA_REFRESH_INTERVAL', '60'))
    fallback_to_kite: bool = os.getenv('FALLBACK_TO_KITE', 'true').lower() == 'true'
    
    # Capital & Margin Management
    max_daily_loss_limit: float = float(os.getenv('MAX_DAILY_LOSS_LIMIT', '5000.0'))
    max_concurrent_positions: int = int(os.getenv('MAX_CONCURRENT_POSITIONS', '5'))
    max_portfolio_risk: float = float(os.getenv('MAX_PORTFOLIO_RISK', '0.02'))
    min_open_interest: int = int(os.getenv('MIN_OPEN_INTEREST', '1000'))
    
    # Backtesting Realism
    slippage_bps: int = int(os.getenv('SLIPPAGE_BPS', '5'))
    enable_slippage_model: bool = os.getenv('ENABLE_SLIPPAGE_MODEL', 'false').lower() == 'true'
    fill_probability_threshold: float = float(os.getenv('FILL_PROBABILITY_THRESHOLD', '0.95'))
    
    # Advanced Monitoring & Alerting
    enable_multi_channel_notifications: bool = os.getenv('ENABLE_MULTI_CHANNEL_NOTIFICATIONS', 'false').lower() == 'true'
    notification_channels: List[str] = field(default_factory=lambda: os.getenv('NOTIFICATION_CHANNELS', 'webhook,telegram').split(','))
    critical_alert_threshold: float = float(os.getenv('CRITICAL_ALERT_THRESHOLD', '0.05'))  # 5% portfolio value
    
    # Strategy Flexibility
    otm_delta_range_conservative_low: float = float(os.getenv('OTM_DELTA_RANGE_CONSERVATIVE_LOW', '0.10'))
    otm_delta_range_conservative_high: float = float(os.getenv('OTM_DELTA_RANGE_CONSERVATIVE_HIGH', '0.15'))
    otm_delta_range_balanced_low: float = float(os.getenv('OTM_DELTA_RANGE_BALANCED_LOW', '0.15'))
    otm_delta_range_balanced_high: float = float(os.getenv('OTM_DELTA_RANGE_BALANCED_HIGH', '0.25'))
    otm_delta_range_aggressive_low: float = float(os.getenv('OTM_DELTA_RANGE_AGGRESSIVE_LOW', '0.25'))
    otm_delta_range_aggressive_high: float = float(os.getenv('OTM_DELTA_RANGE_AGGRESSIVE_HIGH', '0.35'))
    
    # Deployment & DevOps
    enable_health_endpoint: bool = os.getenv('ENABLE_HEALTH_ENDPOINT', 'true').lower() == 'true'
    health_check_interval: int = int(os.getenv('HEALTH_CHECK_INTERVAL', '300'))  # 5 minutes
    log_retention_days: int = int(os.getenv('LOG_RETENTION_DAYS', '30'))
    
    # AI & Advanced Analytics Settings (updated)
    enable_ai_features: bool = os.getenv('ENABLE_AI_FEATURES', 'false').lower() == 'true'
    ai_features: List[str] = field(default_factory=lambda: [f.strip() for f in os.getenv('AI_FEATURES', 'rag,regime,slippage,news,stress,compliance,explain,hedge,whatif').split(',')])
    ai_confidence_threshold: float = float(os.getenv('AI_CONFIDENCE_THRESHOLD', '0.7'))
    semantic_kill_confidence_threshold: float = float(os.getenv('SEMANTIC_KILL_CONFIDENCE_THRESHOLD', '0.9'))
    
    # Additional validation for new safety settings
    def __post_init__(self):
        """Validate configuration parameters after initialization"""
        # Existing validations
        if self.strategy_mode not in ['conservative', 'balanced', 'aggressive']:
            raise ValueError(f"Invalid strategy_mode: {self.strategy_mode}. Must be one of: conservative, balanced, aggressive")
        
        if self.otm_delta_range_low >= self.otm_delta_range_high:
            raise ValueError(f"Delta range low ({self.otm_delta_range_low}) must be less than high ({self.otm_delta_range_high})")
        
        if self.risk_per_trade_percent <= 0 or self.risk_per_trade_percent > 0.10:
            raise ValueError(f"Risk per trade percent ({self.risk_per_trade_percent}) should be between 0 and 0.10 (10%)")
        
        if not self.dry_run and not self.api_key:
            raise ValueError("KITE_API_KEY is required when DRY_RUN is false")
        if not self.dry_run and not self.api_secret:
            raise ValueError("KITE_API_SECRET is required when DRY_RUN is false")
        if not self.dry_run and not self.access_token:
            raise ValueError("KITE_ACCESS_TOKEN is required when DRY_RUN is false")
        
        # New safety validations
        if self.strategy_mode == 'conservative':
            self.otm_delta_range_low = self.otm_delta_range_conservative_low
            self.otm_delta_range_high = self.otm_delta_range_conservative_high
        elif self.strategy_mode == 'aggressive':
            self.otm_delta_range_low = self.otm_delta_range_aggressive_low
            self.otm_delta_range_high = self.otm_delta_range_aggressive_high
        else:  # balanced (default)
            self.otm_delta_range_low = self.otm_delta_range_balanced_low
            self.otm_delta_range_high = self.otm_delta_range_balanced_high
        
        # Validate AI confidence thresholds
        if self.ai_confidence_threshold < 0.0 or self.ai_confidence_threshold > 1.0:
            raise ValueError(f"AI confidence threshold ({self.ai_confidence_threshold}) should be between 0.0 and 1.0")
        
        if self.semantic_kill_confidence_threshold < 0.0 or self.semantic_kill_confidence_threshold > 1.0:
            raise ValueError(f"Semantic kill confidence threshold ({self.semantic_kill_confidence_threshold}) should be between 0.0 and 1.0")
    twilio_auth_token: str = os.getenv('TWILIO_AUTH_TOKEN', '')
    twilio_phone_number: str = os.getenv('TWILIO_PHONE_NUMBER', '')
    voice_max_requests_per_hour: int = int(os.getenv('VOICE_MAX_REQUESTS_PER_HOUR', '10'))
    synth_chain_model_path: str = os.getenv('SYNTH_CHAIN_MODEL_PATH', './ai/models/synth_chain_vae.joblib')
    use_synth_chain: bool = os.getenv('USE_SYNTH_CHAIN', 'false').lower() == 'true'
    allow_synthetic_strikes: bool = os.getenv('ALLOW_SYNTHETIC_STRIKES', 'false').lower() == 'true'
    model_registry_path: str = os.getenv('MODEL_REGISTRY_PATH', './ai/models/registry.json')
    auto_ml_min_data: int = int(os.getenv('AUTO_ML_MIN_DATA', '100'))
    auto_ml_auc_threshold: float = float(os.getenv('AUTO_ML_AUC_THRESHOLD', '0.02'))
    auto_ml_check_interval_hours: int = int(os.getenv('AUTO_ML_CHECK_INTERVAL_HOURS', '24'))
    llm_tests_output_dir: str = os.getenv('LLM_TESTS_OUTPUT_DIR', './tests/llm_generated')
    kelly_fraction: float = float(os.getenv('KELLY_FRACTION', '0.5'))
    kelly_model_path: str = os.getenv('KELLY_MODEL_PATH', './ai/models/kelly_model.pth')
    sentiment_kill_threshold: float = float(os.getenv('SENTIMENT_KILL_THRESHOLD', '-0.7'))
    sentiment_volume_threshold: float = float(os.getenv('SENTIMENT_VOLUME_THRESHOLD', '2.0'))
    patch_issue_template_path: str = os.getenv('PATCH_ISSUE_TEMPLATE_PATH', './issue_template.md')
    patch_suggestions_cache_path: str = os.getenv('PATCH_SUGGESTIONS_CACHE_PATH', './ai/data/patch_suggestions.json')
    embedding_cache_size: int = int(os.getenv('EMBEDDING_CACHE_SIZE', '1000'))
    embedding_cache_ttl: int = int(os.getenv('EMBEDDING_CACHE_TTL', '3600'))
    embedding_lru_size: int = int(os.getenv('EMBEDDING_LRU_SIZE', '100'))
    use_redis_cache: bool = os.getenv('USE_REDIS_CACHE', 'false').lower() == 'true'
    redis_host: str = os.getenv('REDIS_HOST', 'localhost')
    redis_port: int = int(os.getenv('REDIS_PORT', '6379'))
    redis_db: int = int(os.getenv('REDIS_DB', '0'))
    embedding_cache_db_path: str = os.getenv('EMBEDDING_CACHE_DB_PATH', './ai/data/embedding_cache.db')
    semantic_kill_confidence_threshold: float = os.getenv('SEMANTIC_KILL_CONFIDENCE_THRESHOLD', '0.9')
    csv_mapping_db_path: str = os.getenv('CSV_MAPPING_DB_PATH', './ai/data/csv_mappings.db')

    def __post_init__(self):
        """Validate configuration parameters after initialization"""
        # Validate strategy mode
        if self.strategy_mode not in ['conservative', 'balanced', 'aggressive']:
            raise ValueError(f"Invalid strategy_mode: {self.strategy_mode}. Must be one of: conservative, balanced, aggressive")
        
        # Validate delta ranges
        if self.otm_delta_range_low >= self.otm_delta_range_high:
            raise ValueError(f"Delta range low ({self.otm_delta_range_low}) must be less than high ({self.otm_delta_range_high})")
        
        # Validate risk parameters
        if self.risk_per_trade_percent <= 0 or self.risk_per_trade_percent > 0.10:
            raise ValueError(f"Risk per trade percent ({self.risk_per_trade_percent}) should be between 0 and 0.10 (10%)")
        
        # Validate that required API keys are provided when not in dry run mode
        if not self.dry_run and not self.api_key:
            raise ValueError("KITE_API_KEY is required when DRY_RUN is false")
        if not self.dry_run and not self.api_secret:
            raise ValueError("KITE_API_SECRET is required when DRY_RUN is false")
        if not self.dry_run and not self.access_token:
            raise ValueError("KITE_ACCESS_TOKEN is required when DRY_RUN is false")


def get_config() -> OptionWheelConfig:
    """Factory function to create and return a configuration instance"""
    return OptionWheelConfig()


# Create a global config instance
config = get_config()