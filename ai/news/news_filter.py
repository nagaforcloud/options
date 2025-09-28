"""
News Retrieval-Augmented Filter for Options Wheel Strategy Trading Bot
Uses newsapi.org or NSE RSS to filter trades based on news sentiment
"""
from typing import List, Dict, Any, Optional
import feedparser
import requests
import json
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import time

import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logging_utils import logger
from ai.base import is_enabled, call_llm
from ...config.config import config


def fetch_news(
    symbols: List[str], 
    date_range_days: int = 7,
    sources: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Fetch news articles for given symbols
    
    Args:
        symbols: List of trading symbols to fetch news for
        date_range_days: Number of days to look back for news
        sources: Specific news sources to use (optional)
        
    Returns:
        List of news articles with sentiment analysis
    """
    if not is_enabled("news"):
        logger.debug("[AI] News filter is disabled")
        return []
    
    try:
        logger.info(f"[AI] News: Fetching news for symbols: {symbols}")
        
        all_articles = []
        
        # Try multiple news sources
        if sources is None:
            sources = ["nse_rss", "newsapi", "rss_feeds"]
        
        for source in sources:
            try:
                if source == "nse_rss":
                    articles = _fetch_nse_rss_news(symbols, date_range_days)
                elif source == "newsapi" and config.news_api_key:
                    articles = _fetch_newsapi_news(symbols, date_range_days)
                elif source == "rss_feeds":
                    articles = _fetch_generic_rss_news(symbols, date_range_days)
                else:
                    continue
                
                all_articles.extend(articles)
                logger.info(f"[AI] News: Fetched {len(articles)} articles from {source}")
                
            except Exception as e:
                logger.warning(f"[AI] News: Error fetching from {source}: {e}")
                continue
        
        # Remove duplicates and analyze sentiment
        unique_articles = _remove_duplicate_articles(all_articles)
        analyzed_articles = _analyze_article_sentiment(unique_articles)
        
        logger.info(f"[AI] News: Fetched and analyzed {len(analyzed_articles)} unique articles")
        return analyzed_articles
        
    except Exception as e:
        logger.error(f"[AI] News: Error fetching news: {e}")
        return []


def _fetch_nse_rss_news(symbols: List[str], date_range_days: int) -> List[Dict[str, Any]]:
    """
    Fetch news from NSE RSS feeds
    
    Args:
        symbols: List of symbols to fetch news for
        date_range_days: Days to look back
        
    Returns:
        List of news articles
    """
    try:
        # NSE provides various RSS feeds
        rss_urls = [
            "https://www.nseindia.com/wfe/common/rss/corporateActions.xml",
            "https://www.nseindia.com/wfe/common/rss/announcements.xml",
            "https://www.nseindia.com/wfe/common/rss/marketNews.xml"
        ]
        
        articles = []
        cutoff_date = datetime.now() - timedelta(days=date_range_days)
        
        for url in rss_urls:
            try:
                feed = feedparser.parse(url)
                
                for entry in feed.entries:
                    # Parse publication date
                    pub_date = None
                    if hasattr(entry, 'published'):
                        try:
                            pub_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
                        except ValueError:
                            try:
                                pub_date = datetime.strptime(entry.published, '%Y-%m-%dT%H:%M:%SZ')
                            except ValueError:
                                pub_date = datetime.now()
                    
                    # Check if article is within date range
                    if pub_date and pub_date < cutoff_date:
                        continue
                    
                    # Check if article is relevant to any of our symbols
                    title = getattr(entry, 'title', '')
                    summary = getattr(entry, 'summary', '')
                    content = title + ' ' + summary
                    
                    # Simple symbol matching
                    is_relevant = any(symbol.lower() in content.lower() for symbol in symbols)
                    
                    if is_relevant:
                        article = {
                            "source": "NSE RSS",
                            "title": title,
                            "summary": summary,
                            "link": getattr(entry, 'link', ''),
                            "published": pub_date.isoformat() if pub_date else datetime.now().isoformat(),
                            "symbols_mentioned": [s for s in symbols if s.lower() in content.lower()],
                            "content": content
                        }
                        articles.append(article)
                
                # Be respectful to RSS feeds - add delay
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"[AI] News: Error parsing NSE RSS feed {url}: {e}")
                continue
        
        return articles
        
    except Exception as e:
        logger.error(f"[AI] News: Error fetching NSE RSS news: {e}")
        return []


def _fetch_newsapi_news(symbols: List[str], date_range_days: int) -> List[Dict[str, Any]]:
    """
    Fetch news from NewsAPI (if API key available)
    
    Args:
        symbols: List of symbols to fetch news for
        date_range_days: Days to look back
        
    Returns:
        List of news articles
    """
    try:
        if not config.news_api_key:
            logger.debug("[AI] News: NewsAPI key not configured")
            return []
        
        articles = []
        cutoff_date = (datetime.now() - timedelta(days=date_range_days)).strftime('%Y-%m-%d')
        
        for symbol in symbols:
            try:
                # Construct query with symbol
                query = f"{symbol} AND (earnings OR dividends OR merger OR acquisition OR results)"
                encoded_query = quote_plus(query)
                
                # NewsAPI endpoint
                url = f"https://newsapi.org/v2/everything"
                params = {
                    "q": encoded_query,
                    "from": cutoff_date,
                    "sortBy": "publishedAt",
                    "apiKey": config.news_api_key,
                    "language": "en",
                    "pageSize": 20
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for article in data.get('articles', []):
                        pub_date = article.get('publishedAt', datetime.now().isoformat())
                        
                        news_article = {
                            "source": f"NewsAPI ({article.get('source', {}).get('name', 'Unknown')})",
                            "title": article.get('title', ''),
                            "summary": article.get('description', ''),
                            "link": article.get('url', ''),
                            "published": pub_date,
                            "symbols_mentioned": [symbol],
                            "content": article.get('content', ''),
                            "author": article.get('author', ''),
                            "urlToImage": article.get('urlToImage', '')
                        }
                        
                        articles.append(news_article)
                
                # Rate limiting - NewsAPI has rate limits
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"[AI] News: Error fetching NewsAPI news for {symbol}: {e}")
                continue
        
        return articles
        
    except Exception as e:
        logger.error(f"[AI] News: Error fetching NewsAPI news: {e}")
        return []


def _fetch_generic_rss_news(symbols: List[str], date_range_days: int) -> List[Dict[str, Any]]:
    """
    Fetch news from generic financial RSS feeds
    
    Args:
        symbols: List of symbols to fetch news for
        date_range_days: Days to look back
        
    Returns:
        List of news articles
    """
    try:
        # Common financial RSS feeds
        rss_feeds = [
            "https://feeds.reuters.com/reuters/businessNews",
            "https://rss.cnn.com/rss/money_latest.rss",
            "https://feeds.bbci.co.uk/news/business/rss.xml",
            "https://www.business-standard.com/rss/latest.rss"
        ]
        
        articles = []
        cutoff_date = datetime.now() - timedelta(days=date_range_days)
        
        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Parse publication date
                    pub_date = None
                    if hasattr(entry, 'published'):
                        try:
                            pub_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
                        except ValueError:
                            try:
                                pub_date = datetime.strptime(entry.published, '%Y-%m-%dT%H:%M:%SZ')
                            except ValueError:
                                pub_date = datetime.now()
                    
                    # Check if article is within date range
                    if pub_date and pub_date < cutoff_date:
                        continue
                    
                    # Check if article is relevant to any of our symbols
                    title = getattr(entry, 'title', '')
                    summary = getattr(entry, 'summary', '')
                    content = title + ' ' + summary
                    
                    # Simple symbol matching
                    is_relevant = any(symbol.lower() in content.lower() for symbol in symbols)
                    
                    if is_relevant:
                        article = {
                            "source": f"RSS ({getattr(feed.feed, 'title', 'Unknown Source')})",
                            "title": title,
                            "summary": summary,
                            "link": getattr(entry, 'link', ''),
                            "published": pub_date.isoformat() if pub_date else datetime.now().isoformat(),
                            "symbols_mentioned": [s for s in symbols if s.lower() in content.lower()],
                            "content": content
                        }
                        articles.append(article)
                
                # Be respectful to RSS feeds - add delay
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"[AI] News: Error parsing RSS feed {feed_url}: {e}")
                continue
        
        return articles
        
    except Exception as e:
        logger.error(f"[AI] News: Error fetching generic RSS news: {e}")
        return []


def _remove_duplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate articles based on title similarity
    
    Args:
        articles: List of articles to deduplicate
        
    Returns:
        List of unique articles
    """
    try:
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            title = article.get('title', '').lower().strip()
            
            # Simple duplicate detection by title
            if title not in seen_titles:
                unique_articles.append(article)
                seen_titles.add(title)
        
        return unique_articles
        
    except Exception as e:
        logger.error(f"[AI] News: Error deduplicating articles: {e}")
        return articles


def _analyze_article_sentiment(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyze sentiment of news articles using LLM
    
    Args:
        articles: List of articles to analyze
        
    Returns:
        List of articles with sentiment analysis
    """
    try:
        analyzed_articles = []
        
        for article in articles:
            try:
                # Create prompt for sentiment analysis
                prompt = f"""
                You are a financial news sentiment analyzer for the Options Wheel Strategy Trading Bot.
                
                Article to analyze:
                Title: {article.get('title', 'No title')}
                Summary: {article.get('summary', 'No summary')}
                Content: {article.get('content', 'No content')[:500]}...
                
                Analyze this article for its impact on options trading strategies.
                
                Provide sentiment analysis in this JSON format:
                {{
                    "sentiment_score": -1.0 to 1.0,
                    "sentiment_label": "strongly_negative|negative|neutral|positive|strongly_positive",
                    "relevance_score": 0.0 to 1.0,
                    "impact_on_strategy": "high|medium|low|none",
                    "key_themes": ["theme1", "theme2"],
                    "trading_signals": ["signal1", "signal2"],
                    "confidence": 0.0 to 1.0
                }}
                
                Sentiment scoring:
                - -1.0: Extremely negative impact on stocks/options
                - -0.5: Moderately negative
                - 0.0: Neutral/no impact
                - 0.5: Moderately positive
                - 1.0: Extremely positive impact
                
                Consider:
                - Earnings announcements
                - Dividend declarations
                - Merger/Acquisition news
                - Regulatory changes
                - Economic data releases
                - Market-moving events
                """
                
                # Call LLM for sentiment analysis
                response = call_llm(prompt, max_tokens=250, temperature=0.3)
                
                try:
                    import json
                    sentiment_data = json.loads(response)
                except json.JSONDecodeError:
                    # Fallback heuristic analysis
                    sentiment_data = _heuristic_sentiment_analysis(article)
                
                # Add sentiment data to article
                article.update(sentiment_data)
                analyzed_articles.append(article)
                
            except Exception as e:
                logger.warning(f"[AI] News: Error analyzing article sentiment: {e}")
                # Add neutral sentiment as fallback
                article.update({
                    "sentiment_score": 0.0,
                    "sentiment_label": "neutral",
                    "relevance_score": 0.5,
                    "impact_on_strategy": "medium",
                    "key_themes": ["general_market_news"],
                    "trading_signals": ["monitor"],
                    "confidence": 0.3
                })
                analyzed_articles.append(article)
        
        return analyzed_articles
        
    except Exception as e:
        logger.error(f"[AI] News: Error analyzing article sentiment: {e}")
        return articles


def _heuristic_sentiment_analysis(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Heuristic-based sentiment analysis when LLM fails
    
    Args:
        article: Article to analyze
        
    Returns:
        Dictionary with sentiment analysis
    """
    try:
        content = (article.get('title', '') + ' ' + article.get('summary', '') + ' ' + article.get('content', '')).lower()
        
        # Positive keywords
        positive_keywords = [
            'profit', 'gain', 'rise', 'increase', 'boost', 'surge', 'jump', 'climb', 'up',
            'exceed', 'beat', 'outperform', 'strong', 'robust', 'solid', 'growth',
            'positive', 'optimistic', 'confident', 'success', 'achievement'
        ]
        
        # Negative keywords
        negative_keywords = [
            'loss', 'drop', 'fall', 'decline', 'decrease', 'plunge', 'crash', 'collapse',
            'down', 'disappoint', 'miss', 'underperform', 'weak', 'slump', 'downturn',
            'negative', 'concern', 'worry', 'problem', 'issue', 'crisis', 'recession'
        ]
        
        # Count positive and negative words
        positive_count = sum(1 for word in positive_keywords if word in content)
        negative_count = sum(1 for word in negative_keywords if word in content)
        
        # Calculate sentiment score
        total_emotional_words = positive_count + negative_count
        if total_emotional_words > 0:
            sentiment_score = (positive_count - negative_count) / total_emotional_words
        else:
            sentiment_score = 0.0
        
        # Determine sentiment label
        if sentiment_score > 0.5:
            sentiment_label = "positive"
        elif sentiment_score > 0.1:
            sentiment_label = "moderately_positive"
        elif sentiment_score < -0.5:
            sentiment_label = "negative"
        elif sentiment_score < -0.1:
            sentiment_label = "moderately_negative"
        else:
            sentiment_label = "neutral"
        
        # Determine relevance and impact based on content length and keywords
        content_length = len(content)
        relevance_score = min(1.0, content_length / 1000)  # Longer content = more relevant
        impact_score = min(1.0, (positive_count + negative_count) / 20)  # More emotional words = higher impact
        
        # Determine impact on strategy
        if impact_score > 0.7:
            impact_on_strategy = "high"
        elif impact_score > 0.4:
            impact_on_strategy = "medium"
        elif impact_score > 0.2:
            impact_on_strategy = "low"
        else:
            impact_on_strategy = "none"
        
        # Extract key themes (simple keyword extraction)
        themes = []
        if any(word in content for word in ['earnings', 'results', 'profit', 'eps']):
            themes.append('earnings')
        if any(word in content for word in ['dividend', 'dividends']):
            themes.append('dividends')
        if any(word in content for word in ['merger', 'acquisition', 'takeover']):
            themes.append('m&a')
        if any(word in content for word in ['regulat', 'policy', 'law']):
            themes.append('regulatory')
        if any(word in content for word in ['economy', 'gdp', 'inflation', 'rates']):
            themes.append('macro')
        
        if not themes:
            themes = ['general_market_news']
        
        return {
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "relevance_score": relevance_score,
            "impact_on_strategy": impact_on_strategy,
            "key_themes": themes,
            "trading_signals": ["monitor"],
            "confidence": 0.5
        }
        
    except Exception as e:
        logger.error(f"[AI] News: Error in heuristic sentiment analysis: {e}")
        return {
            "sentiment_score": 0.0,
            "sentiment_label": "neutral",
            "relevance_score": 0.3,
            "impact_on_strategy": "low",
            "key_themes": ["general_market_news"],
            "trading_signals": ["monitor"],
            "confidence": 0.2
        }


def filter_trades_based_on_news(
    trades: List[Dict[str, Any]], 
    news_articles: List[Dict[str, Any]],
    time_window_minutes: int = 30
) -> List[Dict[str, Any]]:
    """
    Filter trades that occurred during periods of negative news
    
    Args:
        trades: List of trades to filter
        news_articles: List of news articles with sentiment analysis
        time_window_minutes: Time window to consider news impact (default: 30 minutes)
        
    Returns:
        List of trades potentially impacted by negative news
    """
    if not is_enabled("news"):
        logger.debug("[AI] News filter is disabled")
        return []
    
    try:
        logger.info(f"[AI] News: Filtering {len(trades)} trades based on {len(news_articles)} news articles")
        
        impacted_trades = []
        time_window = timedelta(minutes=time_window_minutes)
        
        for trade in trades:
            try:
                # Parse trade timestamp
                trade_time_str = trade.get('timestamp') or trade.get('order_timestamp') or trade.get('exchange_timestamp')
                if not trade_time_str:
                    continue
                
                try:
                    trade_time = datetime.fromisoformat(trade_time_str.replace('Z', '+00:00'))
                except ValueError:
                    trade_time = datetime.strptime(trade_time_str, '%Y-%m-%d %H:%M:%S')
                
                # Check each news article
                for article in news_articles:
                    # Parse article timestamp
                    article_time_str = article.get('published')
                    if not article_time_str:
                        continue
                    
                    try:
                        article_time = datetime.fromisoformat(article_time_str.replace('Z', '+00:00'))
                    except ValueError:
                        try:
                            article_time = datetime.strptime(article_time_str, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            continue
                    
                    # Check if article is within time window of trade
                    time_diff = abs((trade_time - article_time).total_seconds())
                    if time_diff <= time_window.total_seconds():
                        # Check if article is negative and relevant
                        sentiment_score = article.get('sentiment_score', 0)
                        relevance_score = article.get('relevance_score', 0)
                        symbols_mentioned = article.get('symbols_mentioned', [])
                        trade_symbol = trade.get('symbol', '')
                        
                        # Check if trade symbol is mentioned in article or if it's highly relevant
                        is_relevant = (
                            trade_symbol in symbols_mentioned or 
                            relevance_score > 0.7 or
                            any(symbol in article.get('content', '') for symbol in symbols_mentioned)
                        )
                        
                        # Check if article is negative (sentiment < -0.3) and relevant
                        if sentiment_score < -0.3 and is_relevant:
                            # Add news context to trade
                            trade_copy = trade.copy()
                            trade_copy['news_impact'] = {
                                "article_title": article.get('title', 'Unknown'),
                                "sentiment_score": sentiment_score,
                                "time_difference_minutes": time_diff / 60,
                                "relevance_score": relevance_score,
                                "impact_confidence": article.get('confidence', 0.5)
                            }
                            impacted_trades.append(trade_copy)
                            break  # No need to check other articles for this trade
                
            except Exception as e:
                logger.warning(f"[AI] News: Error processing trade for news filtering: {e}")
                continue
        
        logger.info(f"[AI] News: Identified {len(impacted_trades)} trades potentially impacted by negative news")
        return impacted_trades
        
    except Exception as e:
        logger.error(f"[AI] News: Error filtering trades based on news: {e}")
        return []


def get_news_impact_statistics(
    trades_with_news: List[Dict[str, Any]], 
    all_trades: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate statistics on news impact on trading performance
    
    Args:
        trades_with_news: Trades potentially impacted by negative news
        all_trades: All trades for comparison
        
    Returns:
        Dictionary with impact statistics
    """
    try:
        if not trades_with_news:
            return {
                "news_impact_detected": False,
                "total_trades_analyzed": len(all_trades),
                "news_impacted_trades": 0,
                "impact_percentage": 0.0,
                "statistics": {}
            }
        
        # Calculate P&L for news-impacted trades
        news_pnls = [float(trade.get('pnl', 0)) for trade in trades_with_news]
        all_pnls = [float(trade.get('pnl', 0)) for trade in all_trades]
        
        # Calculate statistics
        avg_news_pnl = sum(news_pnls) / len(news_pnls) if news_pnls else 0
        avg_all_pnl = sum(all_pnls) / len(all_pnls) if all_pnls else 0
        
        # Win rates
        news_wins = len([pnl for pnl in news_pnls if pnl > 0])
        all_wins = len([pnl for pnl in all_pnls if pnl > 0])
        
        news_win_rate = news_wins / len(news_pnls) if news_pnls else 0
        all_win_rate = all_wins / len(all_pnls) if all_pnls else 0
        
        # Max drawdown for news trades
        news_cumulative = []
        cumulative = 0
        for pnl in news_pnls:
            cumulative += pnl
            news_cumulative.append(cumulative)
        
        max_cumulative = 0
        max_drawdown = 0
        for value in news_cumulative:
            max_cumulative = max(max_cumulative, value)
            drawdown = max_cumulative - value
            max_drawdown = max(max_drawdown, drawdown)
        
        statistics = {
            "news_impact_detected": True,
            "total_trades_analyzed": len(all_trades),
            "news_impacted_trades": len(trades_with_news),
            "impact_percentage": len(trades_with_news) / len(all_trades) * 100 if all_trades else 0,
            "average_pnl": {
                "news_impacted": avg_news_pnl,
                "all_trades": avg_all_pnl,
                "difference": avg_news_pnl - avg_all_pnl
            },
            "win_rate": {
                "news_impacted": news_win_rate,
                "all_trades": all_win_rate,
                "difference": news_win_rate - all_win_rate
            },
            "risk_metrics": {
                "max_drawdown_news_trades": max_drawdown,
                "total_news_loss": sum(pnl for pnl in news_pnls if pnl < 0),
                "total_news_profit": sum(pnl for pnl in news_pnls if pnl > 0)
            },
            "comparison_insights": _generate_comparison_insights(avg_news_pnl, avg_all_pnl, news_win_rate, all_win_rate)
        }
        
        return statistics
        
    except Exception as e:
        logger.error(f"[AI] News: Error calculating impact statistics: {e}")
        return {"error": str(e)}


def _generate_comparison_insights(
    avg_news_pnl: float, 
    avg_all_pnl: float, 
    news_win_rate: float, 
    all_win_rate: float
) -> List[str]:
    """
    Generate insights from news impact comparison
    
    Args:
        avg_news_pnl: Average P&L for news-impacted trades
        avg_all_pnl: Average P&L for all trades
        news_win_rate: Win rate for news-impacted trades
        all_win_rate: Win rate for all trades
        
    Returns:
        List of insight statements
    """
    insights = []
    
    if avg_news_pnl < avg_all_pnl:
        difference = ((avg_all_pnl - avg_news_pnl) / abs(avg_all_pnl)) * 100 if avg_all_pnl != 0 else 0
        insights.append(f"News-impacted trades underperformed by {difference:.1f}% on average")
    
    if news_win_rate < all_win_rate:
        difference = (all_win_rate - news_win_rate) * 100
        insights.append(f"News-impacted trades had {difference:.1f}% lower win rate")
    
    if avg_news_pnl < 0 and avg_all_pnl > 0:
        insights.append("News-impacted trades were consistently unprofitable while overall strategy was profitable")
    
    if abs(avg_news_pnl - avg_all_pnl) < abs(avg_all_pnl) * 0.1:  # Within 10%
        insights.append("News impact on performance appears minimal")
    
    return insights


def get_recommended_news_filters() -> Dict[str, Any]:
    """
    Get recommended news-based trading filters
    
    Returns:
        Dictionary with recommended filter settings
    """
    return {
        "sentiment_threshold": -0.3,  # Filter trades when sentiment < -0.3
        "relevance_threshold": 0.6,     # Only consider highly relevant news
        "time_window_minutes": 30,     # 30-minute window for news impact
        "impact_level": "high",        # Only filter on high-impact news
        "symbols_filter": "mentioned", # Filter based on symbols mentioned in news
        "confidence_threshold": 0.7,   # Only trust high-confidence sentiment analysis
        "enabled": is_enabled("news"),
        "last_updated": datetime.now().isoformat()
    }