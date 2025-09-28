#!/bin/bash

# GitHub Push Helper Script
# This script helps push the Options Wheel Strategy Trading Bot to GitHub

set -e  # Exit on any error

echo "🚀 GitHub Push Helper for Options Wheel Strategy Trading Bot"
echo "=========================================================="

# Check if we're in the right directory
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "Please run this script from the Trading directory"
    exit 1
fi

echo "✅ Git repository found"

# Add all files to git
echo "📁 Adding all files to git..."
git add .

# Check if there are changes to commit
if [[ -n $(git status --porcelain) ]]; then
    echo "📝 Creating commit..."
    git commit -m "Initial commit: Options Wheel Strategy Trading Bot for Indian Stock Market

- Complete implementation of Options Wheel Strategy with Cash-Secured Puts and Covered Calls
- All 20 AI-augmented features with proper feature flagging
- Comprehensive safety mechanisms (dry run, live trading confirmation, kill switch)
- Indian market compliance (holiday calendar, timezone enforcement, broker rules)
- Capital and margin management with real-time monitoring
- Market data reliability with fallbacks and caching
- Backtesting realism with transaction costs and slippage modeling
- Advanced monitoring and alerting with multi-channel notifications
- Strategy flexibility with different modes and auto-rolling logic
- Deployment support with Docker, Docker Compose, and systemd
- Comprehensive documentation and testing framework
    
AI Features Implemented:
1. RAG Trade Diary & Chat
2. Regime Detector
3. Generative Stress-Test Engine
4. AI Slippage Predictor
5. Semantic Kill-Switch
6. News Retrieval-Augmented Filter
7. AI Compliance Auditor
8. Multilingual Alerting
9. Voice / WhatsApp Interface
10. Synthetic Option-Chain Imputation
11. Explainable Greeks
12. Auto-Hedge Suggester
13. Smart CSV Column Mapper
14. 'What-If' Scenario Chat
15. Continuous Learning Loop
16. LLM Unit-Test Generator
17. AI-Derived Kelly Position Size
18. Sentiment Kill-Switch
19. AI Code-Patch Suggester
20. Memory-Efficient Embedding Cache

Safety & Compliance Features:
- Dry Run Mode (DRY_RUN=true/false)
- Live Trading Confirmation (prompts 'CONFIRM')
- Kill Switch (STOP_TRADING file check)
- Holiday Calendar Integration (mcal or static NSE list)
- Timezone Enforcement (Asia/Kolkata)
- Broker Compliance Rules (Zerodha product-type alignment)
- Tax & Accounting Hooks (trade_type, tax_category)
- Real-Time Margin Monitoring (kite.margins())
- Dynamic Position Sizing (portfolio risk-based)
- Market Data Reliability (NSE API fallbacks)
- Backtesting Realism (Zerodha F&O charges, slippage)
- Advanced Monitoring (Telegram, Slack, Email, Webhook)
- Strategy Flexibility (modes, auto-rolling)
- Deployment & DevOps (Docker, systemd, documentation)
"
else
    echo "✅ No changes to commit"
fi

# Check if remote exists
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "🔗 Adding remote repository..."
    git remote add origin https://github.com/nagaforcloud/options.git
else
    echo "✅ Remote repository already configured"
    echo "Remote URL: $(git remote get-url origin)"
fi

# Try to push to GitHub
echo "📤 Pushing to GitHub..."

# First, try to fetch and merge any remote changes
echo "🔄 Fetching remote changes..."
if git fetch origin; then
    echo "✅ Fetched remote changes successfully"
else
    echo "⚠️  Warning: Could not fetch remote changes"
fi

# Now push
if git push -u origin master; then
    echo "🎉 Successfully pushed to GitHub!"
    echo "Repository: https://github.com/nagaforcloud/options"
else
    echo "❌ Push failed. Possible reasons:"
    echo "  1. Repository doesn't exist on GitHub yet"
    echo "  2. Authentication required"
    echo "  3. Network connectivity issues"
    echo ""
    echo "Try creating the repository on GitHub first:"
    echo "  1. Go to https://github.com/new"
    echo "  2. Create a new repository named 'options'"
    echo "  3. Make sure it's under the 'nagaforcloud' organization"
    echo "  4. Don't initialize with README"
    echo ""
    echo "Or push with authentication:"
    echo "  git push -u https://<username>:<token>@github.com/nagaforcloud/options.git master"
    exit 1
fi

# Show repository status
echo ""
echo "📊 Repository Status:"
echo "Commits: $(git rev-list --count HEAD)"
echo "Files: $(git ls-files | wc -l)"
echo "Latest commit: $(git log -1 --oneline)"

echo ""
echo "✅ GitHub push completed successfully!"
echo "🎉 The Options Wheel Strategy Trading Bot is now on GitHub!"
echo "🔗 Repository URL: https://github.com/nagaforcloud/options"