# Options Wheel Strategy Trading Bot

## Project Overview

The Options Wheel Strategy Trading Bot is a comprehensive solution for implementing the "Options Wheel Strategy" for the Indian stock market using Zerodha's KiteConnect API. This is a sophisticated income-generating strategy that involves selling out-of-the-money (OTM) options to collect premiums.

## 🛡️ Core Strategy Description

The Options Wheel Strategy works as follows:
1. When not holding the underlying stock, sell OTM Cash-Secured Puts with deltas between 0.15-0.25
2. If assigned (stock delivered), sell OTM Covered Calls on the holdings
3. Manage existing positions with profit targets (typically 50% of premium) and stop-losses (typically 100% of premium)
4. Continuously run during market hours to maximize premium collection

## 🚀 Installation and Setup

### Prerequisites

- Python 3.8+
- Pip package manager
- Zerodha Kite Connect API credentials

### Installation Steps

1. Clone the repository (if using Git):
   ```bash
   git clone <repository-url>
   cd Trading
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. If you want to enable AI features:
   ```bash
   pip install -r requirements-ai.txt
   ```

5. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

6. Edit the `.env` file and add your Zerodha API credentials and other settings:
   ```bash
   KITE_API_KEY=your_api_key_here
   KITE_API_SECRET=your_api_secret_here
   KITE_ACCESS_TOKEN=your_access_token_here
   ```

## ⚙️ Configuration

### Environment Variables

The following environment variables are available in the `.env` file:

#### API Credentials
- `KITE_API_KEY`: Your Kite API key
- `KITE_API_SECRET`: Your Kite API secret
- `KITE_ACCESS_TOKEN`: Your Kite access token

#### Trading Parameters
- `SYMBOL`: Trading symbol (default: TCS)
- `QUANTITY_PER_LOT`: Number of units per lot (default: 150)
- `PROFIT_TARGET_PERCENTAGE`: Profit target as percentage of premium (default: 0.50)
- `LOSS_LIMIT_PERCENTAGE`: Stop loss as percentage of premium (default: 1.00)

#### Delta Range
- `OTM_DELTA_RANGE_LOW`: Lower bound for OTM delta (default: 0.15)
- `OTM_DELTA_RANGE_HIGH`: Upper bound for OTM delta (default: 0.25)

#### Open Interest
- `MIN_OPEN_INTEREST`: Minimum open interest for option selection (default: 1000)

#### Strategy Timing
- `STRATEGY_RUN_INTERVAL_SECONDS`: Interval between strategy cycles (default: 300)
- `MARKET_OPEN_HOUR`: Market open hour (default: 9)
- `MARKET_OPEN_MINUTE`: Market open minute (default: 9)
- `MARKET_CLOSE_HOUR`: Market close hour (default: 15)
- `MARKET_CLOSE_MINUTE`: Market close minute (default: 30)

#### Risk Management
- `MAX_CONCURRENT_POSITIONS`: Maximum concurrent positions (default: 5)
- `MAX_DAILY_LOSS_LIMIT`: Maximum daily loss limit (default: 5000.0)
- `MAX_PORTFOLIO_RISK`: Maximum portfolio risk percentage (default: 0.02)

#### Notification Settings
- `ENABLE_NOTIFICATIONS`: Enable/disable notifications (default: false)
- `NOTIFICATION_WEBHOOK_URL`: Webhook URL for notifications (default: "")
- `NOTIFICATION_TYPE`: Notification type (default: "webhook")
- `TELEGRAM_BOT_TOKEN`: Telegram bot token (default: "")
- `TELEGRAM_CHAT_ID`: Telegram chat ID (default: "")

#### Safety & Compliance Settings
- `DRY_RUN`: Enable dry run mode (default: false)
- `USE_HOLIDAY_CALENDAR`: Use holiday calendar (default: false)
- `HOLIDAY_FILE_PATH`: Path to holiday file (default: ./data/nse_holidays.csv)
- `STRATEGY_MODE`: Strategy mode (conservative, balanced, aggressive) (default: balanced)
- `RISK_PER_TRADE_PERCENT`: Risk per trade as percentage of portfolio (default: 0.01)
- `MIN_CASH_RESERVE`: Minimum cash reserve (default: 10000)
- `ENABLE_AUTO_ROLL`: Enable auto-rolling logic (default: false)
- `KILL_SWITCH_FILE`: Kill switch file name (default: STOP_TRADING)

#### AI & Advanced Analytics Settings
- `ENABLE_AI_FEATURES`: Enable AI features (default: false)
- `AI_FEATURES`: Comma-separated list of AI features to enable (default: "rag,regime,slippage,news,stress,compliance")
- More AI configuration options in the .env file...

## 📊 Usage Examples

### 1. Live Trading Mode

**⚠️ WARNING: This is for educational purposes only. Trading involves significant financial risk.**

```bash
python main.py --mode live
```

For live trading, you'll be prompted with a confirmation message:
```
⚠️ LIVE TRADING MODE ENABLED. Type 'CONFIRM' to proceed:
```

### 2. Backtesting Mode

```bash
python main.py --mode backtest --start-date 2023-01-01 --end-date 2023-03-01
```

### 3. Dashboard Mode

```bash
python main.py --mode dashboard
```

Or directly with Streamlit:
```bash
cd Trading
streamlit run dashboard/dashboard.py
```

### 4. Prepare Data for Backtesting

```bash
python main.py --mode prepare-data
```

## 📊 Dashboard Features

The dashboard provides comprehensive monitoring and analytics:

- **Real-time Portfolio Overview**: Current positions and P&L metrics
- **Performance Charts**: Equity curves and P&L analysis
- **Risk Metrics**: Portfolio risk visualization
- **Strategy Controls**: Start/pause/stop strategy controls
- **Historical Trade Analysis**: Advanced analysis of historical CSV trade data
  - Multi-file CSV loading
  - Date range, year, quarter, and symbol filters
  - Year-over-year and quarter-over-quarter analysis
  - Option Greeks proxy analysis (theta, delta, gamma)

## 🔒 Safety Features

### 1. Dry Run Mode
Set `DRY_RUN=true` to simulate trades without placing real orders. The system will log all orders but never place real trades.

### 2. Live Trading Confirmation
When not in dry run mode, the system prompts:
```
⚠️ LIVE TRADING MODE ENABLED. Type 'CONFIRM' to proceed:
```

### 3. Kill Switch
Create a file named `STOP_TRADING` in the root directory to immediately halt the strategy execution.

### 4. Risk Management
- Daily loss limits
- Position size limits
- Portfolio risk limits
- Margin utilization monitoring
- Maximum concurrent positions

## 🏛️ Indian Market Compliance

- **Holiday Calendar Integration**: Use `mcal` or static NSE holiday list to skip non-trading days
- **Timezone Enforcement**: All datetime operations use `Asia/Kolkata` timezone
- **Broker Compliance Rules**: Enforce Zerodha product-type alignment
- **Tax & Accounting Hooks**: Prepare for future P&L categorization

## 🤖 AI-Augmented Features (20 Modules)

### Available AI Features:
1. RAG Trade Diary & Chat (`rag`)
2. Regime Detector (`regime`) 
3. Generative Stress-Test Engine (`stress`)
4. AI Slippage Predictor (`slippage`)
5. Semantic Kill-Switch (`semantic_kill`)
6. News Retrieval-Augmented Filter (`news`)
7. AI Compliance Auditor (`compliance`)
8. Multilingual Alerting (`i18n`)
9. Voice / WhatsApp Interface (`voice`)
10. Synthetic Option-Chain Imputation (`synth_chain`)
11. Explainable Greeks (`explain`)
12. Auto-Hedge Suggester (`hedge`)
13. Smart CSV Column Mapper (`mapper`)
14. "What-If" Scenario Chat (`whatif`)
15. Continuous Learning Loop (`automl`)
16. LLM Unit-Test Generator (`testgen`)
17. AI-Derived Kelly Position Size (`kelly`)
18. Sentiment Kill-Switch (`sentiment_kill`)
19. AI Code-Patch Suggester (`patch`)
20. Memory-Efficient Embedding Cache (`cache`)

To enable specific AI features:
```bash
export AI_FEATURES=rag,regime,slippage
python main.py
```

## 📁 Folder Structure

```
Trading/
├── .env                           # Environment variables and API keys
├── requirements.txt               # Python dependencies
├── requirements-ai.txt           # Optional AI dependencies
├── IMPLEMENTATION_SUMMARY.md      # Documentation of components
├── TEST_CASES.md                  # Test case specifications
├── README.md                      # This file
├── DEPLOYMENT.md                 # Deployment guide
├── ENHANCEMENTS_SUMMARY.md       # Summary of safety and compliance enhancements
├── run_tests.py                   # Test runner
├── Dockerfile                    # Docker support
├── docker-compose.yml            # Docker Compose configuration
├── docker-compose.dev.yml        # Development Docker Compose override
├── options_wheel_bot.service     # Systemd service file
├── auto_roll_functions.py         # Auto rolling functions
├── basic_functionality_test.py    # Basic functionality tests
├── final_verification.py          # Final verification checks
├── health_check.py                # Health check utilities
├── main.py                        # Main entry point
├── __init__.py
├── __main__.py
├── config/
│   ├── __init__.py
│   └── config.py                  # Configuration management
├── core/
│   ├── __init__.py
│   └── strategy.py                # Core strategy implementation
├── models/
│   ├── __init__.py
│   ├── enums.py                   # Enumerations
│   └── models.py                  # Data models
├── utils/
│   ├── __init__.py
│   └── logging_utils.py           # Logging utilities
├── notifications/
│   ├── __init__.py
│   └── notification_manager.py    # Notification system
├── database/
│   ├── __init__.py
│   └── database.py                # SQLite database for persistence
├── risk_management/
│   ├── __init__.py
│   └── risk_manager.py            # Advanced risk controls
├── dashboard/
│   ├── __init__.py
│   └── dashboard.py               # Web-based dashboard (Streamlit) with advanced analytics
├── backtesting/
│   ├── __init__.py
│   ├── mock_kite.py               # Mock KiteConnect for backtesting
│   ├── nifty_backtesting.py       # NIFTY backtesting
│   ├── nse_data_collector.py      # NSE data collection
│   ├── prepare_nifty_data.py      # NIFTY data preparation script
│   └── sample_data_generator.py   # Sample data generation
├── data/                          # Data files
│   ├── nse_holidays.csv           # NSE holiday calendar (example)
│   └── ...
├── logs/                          # Log files
├── historical_trades/             # Historical trade CSV files
│   └── ...
├── docs/                          # Documentation files
├── ai/                            # AI modules (20 new features)
│   ├── __init__.py
│   ├── base.py                    # AI base functionality
│   ├── rag/
│   ├── regime/
│   ├── slippage/
│   ├── stress/
│   ├── kill/
│   ├── news/
│   ├── compliance/
│   ├── i18n/
│   ├── voice/
│   ├── synth_chain/
│   ├── explain/
│   ├── hedge/
│   ├── mapper/
│   ├── whatif/
│   ├── automl/
│   ├── testgen/
│   ├── kelly/
│   ├── sentiment/
│   ├── patch/
│   └── cache/
├── prompts/                      # AI prompt templates
└── tests/                         # Test files
    ├── __init__.py
    ├── test_config.py
    ├── test_models.py
    ├── test_strategy.py
    ├── test_backtesting.py
    ├── test_integration.py
    ├── test_enhanced.py
    ├── smoke_test.py
    ├── test_ai_features.py        # AI feature tests
    └── README.md
```

## 🧪 Testing

### Running Tests

```bash
python -m pytest tests/
```

Or run the basic functionality tests:

```bash
python basic_functionality_test.py
```

### Final Verification

Run the complete verification suite:

```bash
python final_verification.py
```

## 🚀 Deployment

### Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t options-wheel-bot .
   ```

2. Run with Docker:
   ```bash
   docker run -d --env-file .env options-wheel-bot
   ```

### Docker Compose

1. Start with Docker Compose:
   ```bash
   docker-compose up -d
   ```

### Systemd Service (Linux)

Copy the systemd service file to the appropriate location:

```bash
sudo cp options_wheel_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable options_wheel_bot
sudo systemctl start options_wheel_bot
```

## ⚠️ Important Disclaimers

- This is for educational purposes only - trading involves significant financial risk
- The system should never risk more than the user can afford to lose
- Users must understand all risks before using the system for live trading
- Always test thoroughly in a simulated environment before live trading
- The system should be compliant with Zerodha API terms of service
- All safety features must be thoroughly tested before live deployment
- Users should understand Indian market regulations and tax implications
- AI features are experimental and for analysis only - not for autonomous trading

## 🤝 Contributing

If you'd like to contribute to the project, please fork the repository and create a pull request with your changes. Make sure to follow the existing code structure and add appropriate tests.

## 📄 License

This project is provided as an educational example and should be used responsibly. Trading involves significant risk and you should only risk capital you can afford to lose.