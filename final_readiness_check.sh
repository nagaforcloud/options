#!/bin/bash

# Final Readiness Check for GitHub Push
# This script verifies that the project is ready to be pushed to GitHub

echo "🔍 Final Readiness Check for GitHub Push"
echo "======================================"

# Check if we're in the right directory
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "Please run this script from the Trading directory"
    exit 1
fi

echo "✅ Git repository found"

# Check if we have the required files
required_files=(
    ".env"
    ".env.example"
    ".gitignore"
    "README.md"
    "requirements.txt"
    "requirements-ai.txt"
    "IMPLEMENTATION_SUMMARY.md"
    "TEST_CASES.md"
    "DEPLOYMENT.md"
    "ENHANCEMENTS_SUMMARY.md"
    "main.py"
    "Dockerfile"
    "docker-compose.yml"
    "options_wheel_bot.service"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo "✅ All required files present"
else
    echo "❌ Missing required files:"
    for file in "${missing_files[@]}"; do
        echo "  - $file"
    done
    exit 1
fi

# Check if we have the required directories
required_dirs=(
    "config"
    "core"
    "models"
    "utils"
    "database"
    "risk_management"
    "notifications"
    "dashboard"
    "backtesting"
    "ai"
    "data"
    "logs"
    "historical_trades"
    "docs"
    "tests"
)

missing_dirs=()
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        missing_dirs+=("$dir")
    fi
done

if [ ${#missing_dirs[@]} -eq 0 ]; then
    echo "✅ All required directories present"
else
    echo "❌ Missing required directories:"
    for dir in "${missing_dirs[@]}"; do
        echo "  - $dir"
    done
    exit 1
fi

# Check if we have the AI modules
ai_modules=(
    "ai/rag"
    "ai/regime"
    "ai/slippage"
    "ai/stress"
    "ai/kill"
    "ai/news"
    "ai/compliance"
    "ai/i18n"
    "ai/voice"
    "ai/synth_chain"
    "ai/explain"
    "ai/hedge"
    "ai/mapper"
    "ai/whatif"
    "ai/automl"
    "ai/testgen"
    "ai/kelly"
    "ai/sentiment"
    "ai/patch"
    "ai/cache"
)

missing_ai_modules=()
for module in "${ai_modules[@]}"; do
    if [ ! -d "$module" ]; then
        missing_ai_modules+=("$module")
    fi
done

if [ ${#missing_ai_modules[@]} -eq 0 ]; then
    echo "✅ All AI modules present (${#ai_modules[@]} modules)"
else
    echo "❌ Missing AI modules:"
    for module in "${missing_ai_modules[@]}"; do
        echo "  - $module"
    done
    exit 1
fi

# Check if we have a remote repository
if git remote get-url origin >/dev/null 2>&1; then
    echo "✅ Remote repository configured"
    echo "Remote URL: $(git remote get-url origin)"
else
    echo "⚠️  No remote repository configured (will need to add one before pushing)"
fi

# Check commit history
commit_count=$(git rev-list --count HEAD)
if [ "$commit_count" -gt 0 ]; then
    echo "✅ Git history present ($commit_count commits)"
else
    echo "❌ No commits in repository"
    exit 1
fi

# Check if there are uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    echo "⚠️  Uncommitted changes present - will be included in push"
else
    echo "✅ No uncommitted changes"
fi

echo ""
echo "🎉 Project is ready to be pushed to GitHub!"
echo ""
echo "To push to GitHub, run:"
echo "  git push -u origin master"
echo ""
echo "Or if you need to set up the remote first:"
echo "  git remote add origin https://github.com/nagaforcloud/options.git"
echo "  git push -u origin master"
echo ""
echo "✅ All checks passed - ready for GitHub push!"