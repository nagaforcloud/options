# Options Wheel Strategy Trading Bot

## 🛡️ Overview

The **Options Wheel Strategy Trading Bot** is a comprehensive solution for implementing the "Options Wheel Strategy" for the Indian stock market using Zerodha's KiteConnect API. This sophisticated income-generating strategy involves selling out-of-the-money (OTM) options to collect premiums while maintaining strict safety, compliance, and risk management controls.

## 🚀 Key Features

### 🔐 Safety & Compliance
- **Dry Run Mode**: Add `DRY_RUN=true/false` to `.env`. When enabled, logs all orders but never places real trades. Clearly indicates `[DRY RUN]` in logs and dashboard.
- **Live Trading Confirmation**: On first execution in live mode (`DRY_RUN=false`), prompt user: `⚠️ LIVE TRADING MODE ENABLED. Type 'CONFIRM' to proceed:`. Abort if input ≠ 'CONFIRM'.
- **Kill Switch**: Check for existence of a file (e.g., `STOP_TRADING`) in the root directory. If present, gracefully shut down the strategy loop.
- **Holiday Calendar Integration**: Use `mcal` or static NSE holiday list to skip non-trading days.
- **Timezone Enforcement**: All datetime operations use `Asia/Kolkata`.
- **Broker Compliance Rules**: Enforce Zerodha product-type alignment.
- **Tax & Accounting Hooks**: Track tax categories for future P&L categorization.

### 💰 Capital & Margin Management
- **Real-Time Margin Monitoring**: Before placing any order, call `kite.margins()` to check available cash and utilized debits.
- **Dynamic Position Sizing**: Risk-based sizing: `max_risk = portfolio_value * config.risk_per_trade_percent`.
- **Minimum Cash Reserve**: Maintain minimum cash reserve (`MIN_CASH_RESERVE=10000`).

### 📊 Market Data Reliability
- **Options Chain Fallbacks**: Primary: NSE India API, Fallback: Kite instruments + OHLC data.
- **Delta Approximation**: Estimate delta when real delta unavailable.

### 🧪 Backtesting Realism
- **Transaction Cost Modeling**: Deduct real Zerodha F&O charges per trade.
- **Slippage & Fill Logic**: Apply slippage and only fill if historical bid/ask supports order price.

### 📢 Advanced Monitoring & Alerting
- **Multi-Channel Notifications**: Support Telegram, Slack, Email, Webhook.
- **Critical Alerts**: Send immediate alerts for margin shortfall, daily loss limit breached.
- **Health Endpoint**: In Streamlit dashboard, add `/health` indicator.

### 🔄 Strategy Flexibility
- **Strategy Modes**: Conservative, Balanced, Aggressive modes with different delta ranges.
- **Auto-Rolling Logic**: Before expiry (DTE ≤ 1), auto-roll unprofitable options.

### 🐳 Deployment & DevOps
- **Docker Support**: Dockerfile and docker-compose.yml with volume mounts.
- **Process Management**: Systemd service file for production deployment.
- **Documentation**: Alternatives to `.env` for secrets management.

## 🤖 AI-Augmented Features (20 Modules) ✨

1. **RAG Trade Diary & Chat** (`ai/rag/`) - Natural language querying of historical trade performance
2. **Regime Detector** (`ai/regime/`) - Detects market regimes using FinBERT-India
3. **Generative Stress-Test Engine** (`ai/stress/`) - Generates synthetic market scenarios
4. **AI Slippage Predictor** (`ai/slippage/`) - Predicts order slippage using ML
5. **Semantic Kill-Switch** (`ai/kill/`) - LLM judges Telegram messages for kill intent
6. **News Retrieval-Augmented Filter** (`ai/news/`) - Uses newsapi.org or NSE RSS
7. **AI Compliance Auditor** (`ai/compliance/`) - Nightly job that audits trades
8. **Multilingual Alerting** (`ai/i18n/`) - Accept `LANGUAGE=hi,ta,gu`
9. **Voice / WhatsApp Interface** (`ai/voice/`) - Twilio WhatsApp webhook
10. **Synthetic Option-Chain Imputation** (`ai/synth_chain/`) - VAE trained on historic NSE chains
11. **Explainable Greeks** (`ai/explain/`) - Streamlit widget with plain language
12. **Auto-Hedge Suggester** (`ai/hedge/`) - LLM suggests cheapest offsetting hedge
13. **Smart CSV Column Mapper** (`ai/mapper/`) - LLM maps brokerage CSV headers
14. **"What-If" Scenario Chat** (`ai/whatif/`) - Streamlit chat interface
15. **Continuous Learning Loop** (`ai/automl/`) - Nightly cron that retrains models
16. **LLM Unit-Test Generator** (`ai/testgen/`) - Reads docstrings, generates pytest stubs
17. **AI-Derived Kelly Position Size** (`ai/kelly/`) - Offline RL trained on mock history
18. **Sentiment Kill-Switch** (`ai/sentiment/`) - Aggregates Twitter & Reddit sentiment
19. **AI Code-Patch Suggester** (`ai/patch/`) - On unhandled exception, suggests patch
20. **Memory-Efficient Embedding Cache** (`ai/cache/`) - LRU cache for embeddings

## 📈 Dashboard Features

### Enhanced Dashboard with Historical Trade Analysis
- **Real-time Portfolio Overview**: Current positions and P&L metrics
- **Multiple Tabs Structure**: Overview, Positions, Trades, Historical Trades, Performance, Risk, Controls, AI Insights, Strategy Lab
- **Historical Trade Analysis**: Advanced analysis of historical CSV trade data
- **Multi-File CSV Loading**: Automatically discovers and combines tradebook CSV files
- **Advanced Filtering System**: Date range, Year, Quarter, Symbol filters
- **Year-over-Year Analysis**: Performance comparison charts by year
- **Quarter-over-Quarter Analysis**: Performance comparison charts by quarter
- **Option Greeks Analysis**: Theta, Delta, Gamma proxy analysis
- **Interactive Charts**: Cumulative performance, Daily trade volume, YoY/QoQ comparisons
- **Data Table**: Historical trades with source file and directory information

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Zerodha Kite Connect API credentials
- Docker (optional, for containerized deployment)

### Setup
```bash
# Clone the repository
git clone https://github.com/nagaforcloud/options.git
cd options

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-ai.txt  # For AI features (optional)

# Configure environment
cp .env.example .env
# Edit .env with your Zerodha API credentials and other settings
```

### Configuration
Edit the `.env` file with your Zerodha API credentials:
```
# API Credentials
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
KITE_ACCESS_TOKEN=your_access_token_here

# Trading Parameters
SYMBOL=TCS
QUANTITY_PER_LOT=150
PROFIT_TARGET_PERCENTAGE=0.50
LOSS_LIMIT_PERCENTAGE=1.00
OTM_DELTA_RANGE_LOW=0.15
OTM_DELTA_RANGE_HIGH=0.25
MIN_OPEN_INTEREST=1000

# Strategy Timing
STRATEGY_RUN_INTERVAL_SECONDS=300
MARKET_OPEN_HOUR=9
MARKET_OPEN_MINUTE=9  # Changed from 15 to match actual config
MARKET_CLOSE_HOUR=15
MARKET_CLOSE_MINUTE=30

# Risk Management
MAX_CONCURRENT_POSITIONS=5
MAX_DAILY_LOSS_LIMIT=5000.0
MAX_PORTFOLIO_RISK=0.02

# Notification Settings
ENABLE_NOTIFICATIONS=false
NOTIFICATION_WEBHOOK_URL=
NOTIFICATION_TYPE=webhook

# Data Settings
USE_NSE_API=true
DATA_REFRESH_INTERVAL=60
USE_NIFTY=false

# Safety & Compliance Settings
DRY_RUN=false
USE_HOLIDAY_CALENDAR=false
HOLIDAY_FILE_PATH=./data/nse_holidays.csv
STRATEGY_MODE=balanced
RISK_PER_TRADE_PERCENT=0.01
MIN_CASH_RESERVE=10000
ENABLE_AUTO_ROLL=false
KILL_SWITCH_FILE=STOP_TRADING

# AI & Advanced Analytics Settings
ENABLE_AI_FEATURES=false
AI_FEATURES=rag,regime,slippage,news,stress,compliance
AI_MODEL_DIR=./data/ai_models
AI_RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
AI_LLM_MODEL=llama3:8b
AI_LLM_BASE_URL=http://localhost:11434
AI_LLM_TIMEOUT=30
AI_MAX_CONTEXT_DAYS=90
AI_CONFIDENCE_THRESHOLD=0.7
AI_DECISION_LOGGING=false
VECTOR_DB_PATH=./ai/data/chroma.sqlite3
OPENAI_API_KEY=
RAG_CONFIDENCE_THRESHOLD=0.7
REGIME_LOOKBACK_DAYS=30
REGIME_CONFIDENCE_THRESHOLD=0.7
SLIPPAGE_BPS=5
SLIPPAGE_MODEL_PATH=./ai/models/slippage_model.joblib
SLIPPAGE_SCALER_PATH=./ai/models/slippage_scaler.joblib
STRESS_DB_PATH=./ai/data/stress_results.db
NEWS_VECTOR_DB_PATH=./ai/data/news_chroma.sqlite3
COMPLIANCE_REPORTS_DIR=./compliance_reports
ALERT_LANGUAGE=en
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
VOICE_MAX_REQUESTS_PER_HOUR=10
SYNTH_CHAIN_MODEL_PATH=./ai/models/synth_chain_vae.joblib
USE_SYNTH_CHAIN=false
ALLOW_SYNTHETIC_STRIKES=false
MODEL_REGISTRY_PATH=./ai/models/registry.json
AUTO_ML_MIN_DATA=100
AUTO_ML_AUC_THRESHOLD=0.02
AUTO_ML_CHECK_INTERVAL_HOURS=24
LLM_TESTS_OUTPUT_DIR=./tests/llm_generated
KELLY_FRACTION=0.5
KELLY_MODEL_PATH=./ai/models/kelly_model.pth
SENTIMENT_KILL_THRESHOLD=-0.7
SENTIMENT_VOLUME_THRESHOLD=2.0
PATCH_ISSUE_TEMPLATE_PATH=./issue_template.md
PATCH_SUGGESTIONS_CACHE_PATH=./ai/data/patch_suggestions.json
EMBEDDING_CACHE_SIZE=1000
EMBEDDING_CACHE_TTL=3600
EMBEDDING_LRU_SIZE=100
USE_REDIS_CACHE=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
EMBEDDING_CACHE_DB_PATH=./ai/data/embedding_cache.db
SEMANTIC_KILL_CONFIDENCE_THRESHOLD=0.9
CSV_MAPPING_DB_PATH=./ai/data/csv_mappings.db

# Additional Settings
INCLUDE_FEES_IN_BACKTEST=true
```

## ▶️ Usage

### Live Trading Mode
```bash
# First-time setup - will prompt for confirmation
python main.py --mode live

# Subsequent runs
python main.py --mode live
```

### Backtesting Mode
```bash
# Run backtesting
python main.py --mode backtest --start-date 2023-01-01 --end-date 2023-03-01
```

### Dashboard Mode
```bash
# Run Streamlit dashboard
streamlit run dashboard/dashboard.py
```

### Prepare Data for Backtesting
```bash
# Prepare historical data
python main.py --mode prepare-data
```

## 🐳 Docker Deployment

### Using Docker
```bash
# Build the image
docker build -t options-wheel-bot .

# Run the container
docker run -d --env-file .env -p 8501:8501 --name options-wheel-bot options-wheel-bot
```

### Using Docker Compose
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📚 Documentation

- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical implementation details
- [TEST_CASES.md](TEST_CASES.md) - Test case specifications
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [ENHANCEMENTS_SUMMARY.md](ENHANCEMENTS_SUMMARY.md) - Safety and compliance enhancements
- [FINAL_SUMMARY.md](FINAL_SUMMARY.md) - Final project summary

## ⚠️ Disclaimer

This software is for educational purposes only. Trading involves significant financial risk, and you should only risk capital you can afford to lose. The authors are not responsible for any financial losses incurred through the use of this software.

Always test thoroughly in a simulated environment before using for live trading. Understand all risks associated with options trading before implementing any strategy.

## 🤝 Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

## 📄 License

This project is provided as an educational example and should be used responsibly. Trading involves significant risk and you should only risk capital you can afford to lose.