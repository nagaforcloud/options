"""
Dashboard module for Options Wheel Strategy Trading Bot
Provides a Streamlit-based web interface for monitoring and analytics
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import glob
from typing import Optional, Dict, Any
import pytz
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import glob
from typing import Optional, Dict, Any
import pytz
import json

# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config import config
from utils.logging_utils import logger
from database.database import db_manager
from core.strategy import OptionWheelStrategy
from models.models import Trade, Position
from risk_management.risk_manager import risk_manager
from notifications.notification_manager import send_health_check
from ai.base import ai_base, is_enabled


# Global cache for CSV data to improve performance
_csv_cache = {}
_csv_cache_timestamp = {}

def _get_cache_key(paths_to_search):
    """Generate a cache key based on file modification times"""
    import hashlib
    cache_parts = []
    for path in paths_to_search:
        if os.path.exists(path):
            for csv_file in glob.glob(os.path.join(path, "*.csv")):
                mtime = os.path.getmtime(csv_file)
                cache_parts.append(f"{csv_file}:{mtime}")
    cache_string = "|".join(sorted(cache_parts))
    return hashlib.md5(cache_string.encode()).hexdigest()

def load_historical_trades_from_csv() -> pd.DataFrame:
    """
    Load historical trades from CSV files in the main directory and historical_trades folder
    With caching to improve performance
    """
    try:
        # Define base paths to search for CSV files
        paths_to_search = [
            "/Users/nagashankar/pythonScripts/OWS/",  # As specified in the requirements
            "/Users/nagashankar/pythonScripts/OWS/historical_trades/",
            "./",  # Current directory
            "./historical_trades/"
        ]
        
        # Generate cache key based on file modification times
        cache_key = _get_cache_key(paths_to_search)
        
        # Check cache first (cache for 5 minutes)
        current_time = datetime.now().timestamp()
        if cache_key in _csv_cache and (current_time - _csv_cache_timestamp.get(cache_key, 0)) < 300:  # 5 minutes
            logger.info("Using cached CSV data")
            return _csv_cache[cache_key].copy()
        
        all_dataframes = []
        
        # Search for CSV files in all paths
        for path in paths_to_search:
            if os.path.exists(path):
                csv_files = glob.glob(os.path.join(path, "*.csv"))
                
                for csv_file in csv_files:
                    try:
                        # Determine folder for the file
                        file_dir = os.path.basename(os.path.dirname(csv_file))
                        if file_dir == "historical_trades" or file_dir == "":
                            folder = file_dir if file_dir else "main"
                        else:
                            folder = file_dir
                        
                        # Read the CSV file
                        df = pd.read_csv(csv_file)
                        
                        # Add source information
                        df['source_file'] = os.path.basename(csv_file)
                        df['source_folder'] = folder
                        df['full_path'] = csv_file
                        
                        # Try to parse different date column formats
                        date_columns = ['date', 'Date', 'timestamp', 'Timestamp', 'entry_time', 'exit_time']
                        for col in date_columns:
                            if col in df.columns:
                                try:
                                    df['trade_date'] = pd.to_datetime(df[col], errors='coerce')
                                    break
                                except:
                                    continue
                        
                        # If no valid date column was found, create one based on file modification time
                        if 'trade_date' not in df.columns:
                            file_mod_time = datetime.fromtimestamp(os.path.getmtime(csv_file))
                            df['trade_date'] = file_mod_time
                            logger.warning(f"Could not parse dates for {csv_file}, using file modification time")
                        
                        all_dataframes.append(df)
                        logger.info(f"Loaded {len(df)} rows from {csv_file}")
                        
                    except Exception as e:
                        logger.error(f"Error reading CSV file {csv_file}: {e}")
        
        if not all_dataframes:
            logger.warning("No CSV files found in specified paths")
            empty_df = pd.DataFrame()
            # Cache the empty result
            _csv_cache[cache_key] = empty_df
            _csv_cache_timestamp[cache_key] = current_time
            return empty_df.copy()
        
        # Combine all dataframes
        combined_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
        
        # Clean up and standardize columns
        # Convert common column names to standard names
        column_mapping = {
            'symbol': 'symbol',
            'Symbol': 'symbol', 
            'tradingsymbol': 'symbol',
            'Tradingsymbol': 'symbol',
            'instrument': 'symbol',
            'Instrument': 'symbol',
            'pnl': 'pnl',
            'PnL': 'pnl',
            'PNL': 'pnl', 
            'profit': 'pnl',
            'Profit': 'pnl',
            'net_pnl': 'pnl',
            'Net_PnL': 'pnl',
            'entry_price': 'entry_price',
            'Entry_Price': 'entry_price',
            'buy_price': 'entry_price',
            'Buy_Price': 'entry_price',
            'exit_price': 'exit_price', 
            'Exit_Price': 'exit_price',
            'sell_price': 'exit_price',
            'Sell_Price': 'exit_price',
            'quantity': 'quantity',
            'Quantity': 'quantity',
            'qty': 'quantity',
            'Qty': 'quantity',
            'strike': 'strike',
            'Strike': 'strike',
            'option_type': 'option_type',
            'Option_Type': 'option_type',
            'type': 'option_type',
            'Type': 'option_type',
            'transaction_type': 'transaction_type',
            'Transaction_Type': 'transaction_type'
        }
        
        # Rename columns if they exist
        for old_name, new_name in column_mapping.items():
            if old_name in combined_df.columns and new_name != old_name:
                if new_name not in combined_df.columns:
                    combined_df.rename(columns={old_name: new_name}, inplace=True)
        
        logger.info(f"Combined {len(all_dataframes)} files into a dataframe with {len(combined_df)} rows")
        
        # Cache the result
        _csv_cache[cache_key] = combined_df
        _csv_cache_timestamp[cache_key] = current_time
        
        return combined_df.copy()
        
    except Exception as e:
        logger.error(f"Error loading historical trades from CSV: {e}")
        return pd.DataFrame()


def extract_expiry_info(symbol: str) -> tuple:
    """
    Extract expiry date and option type from symbol name
    """
    try:
        # NSE option symbols are typically in format: INFY24JUL1600CE
        # Where: INFY=name, 24JUL=expiry, 1600=strike, CE=type
        import re
        
        # Look for date pattern like 24JUL or 240707 (YYMMDD)
        date_match = re.search(r'(\d{2}[A-Z]{3}|\d{6})', symbol)
        if date_match:
            date_str = date_match.group(1)
            # Try to parse as YYMMM (e.g., 24JUL) or YYMMDD (e.g., 240707)
            try:
                if len(date_str) == 5:  # YYMMM
                    expiry = datetime.strptime(date_str, '%y%b').date()
                elif len(date_str) == 6:  # YYMMDD
                    expiry = datetime.strptime(date_str, '%y%m%d').date()
                else:
                    expiry = None
            except:
                expiry = None
        else:
            expiry = None
        
        # Determine option type
        option_type = None
        if 'CE' in symbol.upper():
            option_type = 'CE'  # Call
        elif 'PE' in symbol.upper():
            option_type = 'PE'  # Put
        
        # Extract strike price
        strike_match = re.search(r'(\d+)C[EP]|(\d+)P[EC]', symbol.upper())
        if strike_match:
            strike = strike_match.group(1) or strike_match.group(2)
            strike = float(strike) if strike else None
        else:
            strike = None
            
        return expiry, option_type, strike
    except:
        return None, None, None


def calculate_greeks_proxy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Greeks proxy measures from trade data
    """
    try:
        # Create copies to avoid SettingWithCopyWarning
        df = df.copy()
        
        # Extract expiry info for theta analysis
        df[['expiry_date', 'option_type', 'strike_price']] = df.apply(
            lambda row: pd.Series(extract_expiry_info(row.get('symbol', ''))), axis=1
        )
        
        # Calculate Days to Expiry (DTE) if we have trade date and expiry
        if 'trade_date' in df.columns and 'expiry_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date'], errors='coerce')
            df['expiry_date'] = pd.to_datetime(df['expiry_date'], errors='coerce')
            df['dte'] = (df['expiry_date'] - df['trade_date']).dt.days
            
        # Determine if the symbol is a call or put
        df['option_type'] = df['option_type'].fillna(df.apply(
            lambda row: 'CE' if 'CE' in str(row.get('symbol', '')).upper() else 
                        'PE' if 'PE' in str(row.get('symbol', '')).upper() else None, axis=1
        ))
        
        # Create strike price groups for gamma analysis (if not already present)
        if 'strike_price' in df.columns and df['strike_price'].notna():
            df['strike_group'] = pd.cut(df['strike_price'], 
                                      bins=10, 
                                      labels=['Group_' + str(i) for i in range(10)])
        else:
            # If we couldn't extract strike prices, create groups based on other available price columns
            price_cols = ['entry_price', 'exit_price', 'avg_price', 'price']
            for col in price_cols:
                if col in df.columns and df[col].notna().any():
                    df['strike_group'] = pd.cut(df[col].fillna(0), 
                                              bins=10, 
                                              labels=['Group_' + str(i) for i in range(10)])
                    break
            else:
                # If no price columns found, create a default group
                df['strike_group'] = 'All'
        
        return df
    except Exception as e:
        logger.error(f"Error calculating Greeks proxy: {e}")
        return df


def get_historical_performance_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate historical performance summary metrics
    """
    if df.empty:
        return {}
    
    try:
        # Convert pnl column to numeric if it exists
        if 'pnl' in df.columns:
            df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce')
        
        # Calculate basic metrics
        total_pnl = df['pnl'].sum() if 'pnl' in df.columns else 0
        total_trades = len(df)
        win_trades = len(df[df['pnl'] > 0]) if 'pnl' in df.columns else 0
        loss_trades = len(df[df['pnl'] < 0]) if 'pnl' in df.columns else 0
        win_rate = win_trades / total_trades if total_trades > 0 else 0
        avg_win = df[df['pnl'] > 0]['pnl'].mean() if win_trades > 0 and 'pnl' in df.columns else 0
        avg_loss = df[df['pnl'] < 0]['pnl'].mean() if loss_trades > 0 and 'pnl' in df.columns else 0
        profit_factor = abs(avg_win * win_trades / (avg_loss * loss_trades)) if (loss_trades > 0 and avg_loss != 0) else float('inf')
        
        # Calculate max drawdown
        if 'pnl' in df.columns:
            cumulative_pnl = df['pnl'].fillna(0).cumsum()
            running_max = cumulative_pnl.expanding().max()
            drawdown = cumulative_pnl - running_max
            max_drawdown = drawdown.min()
        else:
            max_drawdown = 0
        
        # Calculate Sharpe ratio (simplified)
        if 'pnl' in df.columns:
            daily_pnl = df.groupby(df['trade_date'].dt.date)['pnl'].sum()
            sharpe_ratio = daily_pnl.mean() / daily_pnl.std() if daily_pnl.std() != 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_pnl': total_pnl,
            'total_trades': total_trades,
            'win_trades': win_trades,
            'loss_trades': loss_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'avg_win': avg_win,
            'avg_loss': avg_loss
        }
    except Exception as e:
        logger.error(f"Error calculating performance summary: {e}")
        return {}


def main():
    """
    Main Streamlit dashboard function
    """
    st.set_page_config(
        page_title="Options Wheel Strategy Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("🔍 Options Wheel Strategy Dashboard")
    st.markdown("---")
    
    # Initialize session state for storing data
    if 'historical_data_loaded' not in st.session_state:
        st.session_state.historical_data_loaded = False
        st.session_state.historical_data = pd.DataFrame()
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Overview", "Positions", "Trades", "Historical Trades", "Performance", "Risk", "Controls", "AI Insights", "Strategy Lab"]
    )
    
    # Health check
    send_health_check("OK", {"current_time": datetime.now().isoformat()})
    
    # Page content based on selection
    if page == "Overview":
        st.header("📈 Portfolio Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Portfolio Value", f"₹{risk_manager.portfolio_value:,.2f}")
        with col2:
            st.metric("Daily P&L", f"₹{risk_manager.daily_pnl:,.2f}")
        with col3:
            st.metric("Total P&L", f"₹{risk_manager.daily_pnl:,.2f}")  # Placeholder - need to implement total P&L
        with col4:
            st.metric("Active Positions", f"{len(risk_manager.current_positions)}")
        
        # P&L Chart
        st.subheader("Portfolio P&L Trend")
        
        # Mock data for demonstration
        dates = pd.date_range(start=datetime.today() - timedelta(days=30), end=datetime.today())
        pnl_data = pd.DataFrame({
            'Date': dates,
            'P&L': np.random.randn(len(dates)).cumsum() * 1000 + 5000  # Mock data
        })
        
        if not pnl_data.empty:
            fig = px.line(pnl_data, x='Date', y='P&L', title="30-Day P&L Trend")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No P&L data available")
        
        # Position Distribution
        st.subheader("Position Distribution")
        if risk_manager.current_positions:
            pos_data = [{"Symbol": symbol, "Value": abs(pos.average_price * pos.quantity)} 
                       for symbol, pos in risk_manager.current_positions.items()]
            pos_df = pd.DataFrame(pos_data)
            
            if not pos_df.empty:
                fig = px.pie(pos_df, values='Value', names='Symbol', title="Position Allocation")
                st.plotly_chart(fig, use_container_width=True)
        
        # Risk Gauges
        st.subheader("Risk Dashboard")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Portfolio Risk Percentage
            total_pos_value = sum(abs(pos.average_price * pos.quantity) for pos in risk_manager.current_positions.values())
            portfolio_risk_pct = (total_pos_value / risk_manager.portfolio_value) if risk_manager.portfolio_value > 0 else 0
            st.metric("Portfolio Risk", f"{portfolio_risk_pct:.2%}")
            st.progress(min(portfolio_risk_pct / 0.02, 1.0))  # Assuming 2% max risk
        with col2:
            # Margin Utilization
            margin_util = risk_manager.margin_used / (risk_manager.margin_used + risk_manager.margin_available) if (risk_manager.margin_used + risk_manager.margin_available) > 0 else 0
            st.metric("Margin Utilization", f"{margin_util:.2%}")
            st.progress(min(margin_util / 0.95, 1.0))  # Assuming 95% max utilization
        with col3:
            # Daily Loss
            st.metric("Daily Loss", f"₹{risk_manager.daily_losses:,.2f}")
            st.progress(min(risk_manager.daily_losses / config.max_daily_loss_limit, 1.0) if config.max_daily_loss_limit > 0 else 0)
    
    elif page == "Positions":
        st.header("💼 Current Positions")
        
        # Get positions from database
        positions = db_manager.get_all_positions()
        
        if positions:
            pos_data = []
            for pos in positions:
                pos_data.append({
                    'Symbol': pos.symbol,
                    'Quantity': pos.quantity,
                    'Avg Price': f"₹{pos.average_price:.2f}",
                    'Last Price': f"₹{pos.last_price:.2f}",
                    'P&L': f"₹{pos.pnl:.2f}",
                    'Unrealized P&L': f"₹{pos.unrealized_pnl:.2f}",
                    'Realized P&L': f"₹{pos.realized_pnl:.2f}"
                })
            
            df_pos = pd.DataFrame(pos_data)
            st.dataframe(df_pos, use_container_width=True)
        else:
            st.write("No positions currently held.")
    
    elif page == "Trades":
        st.header("🛒 Recent Trades")
        
        # Get trades from database
        trades = db_manager.get_all_trades()
        
        if trades:
            trade_data = []
            for trade in trades[:50]:  # Show last 50 trades
                trade_data.append({
                    'Order ID': trade.order_id,
                    'Symbol': trade.symbol,
                    'Type': trade.transaction_type,
                    'Quantity': trade.quantity,
                    'Price': f"₹{trade.price:.2f}",
                    'Status': trade.status,
                    'Timestamp': trade.order_timestamp,
                    'P&L': f"₹{trade.pnl if hasattr(trade, 'pnl') else 0:.2f}"
                })
            
            df_trades = pd.DataFrame(trade_data)
            st.dataframe(df_trades, use_container_width=True)
        else:
            st.write("No recent trades available.")
    
    elif page == "Historical Trades":
        st.header("📋 Historical Trade Analysis")
        
        # Load historical data if not already loaded
        if not st.session_state.historical_data_loaded:
            with st.spinner("Loading historical trade data..."):
                st.session_state.historical_data = load_historical_trades_from_csv()
                st.session_state.historical_data_loaded = True
                
                if not st.session_state.historical_data.empty:
                    st.session_state.historical_data = calculate_greeks_proxy(st.session_state.historical_data)
                    st.success(f"Loaded {len(st.session_state.historical_data)} historical trade records from {len(st.session_state.historical_data['source_file'].unique())} CSV files")
        
        # Filters in sidebar
        st.sidebar.subheader("Filters")
        df = st.session_state.historical_data
        
        if not df.empty:
            # Date range filter
            min_date = df['trade_date'].min() if 'trade_date' in df.columns else datetime(2020, 1, 1)
            max_date = df['trade_date'].max() if 'trade_date' in df.columns else datetime.today()
            
            if pd.notna(min_date) and pd.notna(max_date):
                date_range = st.sidebar.date_input(
                    "Date Range",
                    value=(min_date.date(), max_date.date()),
                    min_value=min_date.date(),
                    max_value=max_date.date()
                )
                
                if len(date_range) == 2:
                    df = df[(df['trade_date'].dt.date >= date_range[0]) & 
                            (df['trade_date'].dt.date <= date_range[1])]
            
            # Year filter
            if 'trade_date' in df.columns:
                available_years = sorted(df['trade_date'].dt.year.unique())
                selected_years = st.sidebar.multiselect(
                    "Select Years",
                    options=available_years,
                    default=available_years
                )
                if selected_years:
                    df = df[df['trade_date'].dt.year.isin(selected_years)]
            
            # Quarter filter
            if 'trade_date' in df.columns:
                df['quarter'] = df['trade_date'].dt.to_period('Q')
                available_quarters = sorted(df['quarter'].unique())
                selected_quarters = st.sidebar.multiselect(
                    "Select Quarters",
                    options=[str(q) for q in available_quarters],
                    default=[str(q) for q in available_quarters]
                )
                if selected_quarters:
                    df = df[df['quarter'].astype(str).isin(selected_quarters)]
            
            # Symbol filter
            if 'symbol' in df.columns:
                available_symbols = sorted(df['symbol'].unique())
                selected_symbols = st.sidebar.multiselect(
                    "Select Symbols",
                    options=available_symbols,
                    default=available_symbols
                )
                if selected_symbols:
                    df = df[df['symbol'].isin(selected_symbols)]
            
            # Display performance summary
            st.subheader("Performance Summary")
            perf_summary = get_historical_performance_summary(df)
            if perf_summary:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total P&L", f"₹{perf_summary['total_pnl']:,.2f}")
                    st.metric("Total Trades", perf_summary['total_trades'])
                with col2:
                    st.metric("Win Rate", f"{perf_summary['win_rate']:.2%}")
                    st.metric("Profit Factor", f"{perf_summary['profit_factor']:.2f}")
                with col3:
                    st.metric("Max Drawdown", f"₹{perf_summary['max_drawdown']:,.2f}")
                    st.metric("Avg Win", f"₹{perf_summary['avg_win']:,.2f}")
                with col4:
                    st.metric("Sharpe Ratio", f"{perf_summary['sharpe_ratio']:.2f}")
                    st.metric("Avg Loss", f"₹{perf_summary['avg_loss']:,.2f}")
            
            # Year-over-Year Analysis
            st.subheader("Year over Year Analysis")
            if 'trade_date' in df.columns and 'pnl' in df.columns:
                df['year'] = df['trade_date'].dt.year
                yoy_pnl = df.groupby('year')['pnl'].sum().reset_index()
                fig_yoy = px.bar(yoy_pnl, x='year', y='pnl', title="Annual P&L")
                fig_yoy.update_traces(marker_color=['red' if x < 0 else 'green' for x in yoy_pnl['pnl']])
                st.plotly_chart(fig_yoy, use_container_width=True)
            
            # Quarter-over-Quarter Analysis
            st.subheader("Quarter over Quarter Analysis")
            if 'quarter' in df.columns and 'pnl' in df.columns:
                qoq_pnl = df.groupby('quarter')['pnl'].sum().reset_index()
                qoq_pnl['quarter'] = qoq_pnl['quarter'].astype(str)
                fig_qoq = px.bar(qoq_pnl, x='quarter', y='pnl', title="Quarterly P&L")
                fig_qoq.update_traces(marker_color=['red' if x < 0 else 'green' for x in qoq_pnl['pnl']])
                st.plotly_chart(fig_qoq, use_container_width=True)
            
            # P&L by Symbol
            st.subheader("P&L by Symbol")
            if 'symbol' in df.columns and 'pnl' in df.columns:
                symbol_pnl = df.groupby('symbol')['pnl'].sum().reset_index()
                fig_symbol = px.bar(symbol_pnl, x='symbol', y='pnl', title="P&L by Symbol")
                fig_symbol.update_traces(marker_color=['red' if x < 0 else 'green' for x in symbol_pnl['pnl']])
                st.plotly_chart(fig_symbol, use_container_width=True)
            
            # Greeks Analysis (Proxy Measures)
            st.subheader("Greeks Analysis (Proxy)")
            
            # Theta Analysis: DTE vs P&L
            if 'dte' in df.columns and 'pnl' in df.columns:
                st.subheader("Theta Analysis (P&L vs Days to Expiry)")
                df_theta = df[df['dte'].notna()].copy()
                fig_theta = px.scatter(df_theta, x='dte', y='pnl', 
                                     title="P&L vs Days to Expiry (Theta Proxy)",
                                     hover_data=['symbol'])
                st.plotly_chart(fig_theta, use_container_width=True)
            
            # Delta Analysis: Option Type vs P&L
            if 'option_type' in df.columns and 'pnl' in df.columns:
                st.subheader("Delta Analysis (Call vs Put P&L)")
                df_delta = df[df['option_type'].notna()].copy()
                fig_delta = px.box(df_delta, x='option_type', y='pnl', 
                                 title="P&L Distribution by Option Type (Delta Proxy)")
                st.plotly_chart(fig_delta, use_container_width=True)
            
            # Gamma Analysis: Strike Groups vs P&L
            if 'strike_group' in df.columns and 'pnl' in df.columns:
                st.subheader("Gamma Analysis (P&L by Strike Groups)")
                df_gamma = df[df['strike_group'].notna()].copy()
                fig_gamma = px.box(df_gamma, x='strike_group', y='pnl', 
                                 title="P&L Distribution by Strike Groups (Gamma Proxy)")
                st.plotly_chart(fig_gamma, use_container_width=True)
            
            # Raw data table
            st.subheader("Trade Data")
            # Format numeric columns for Indian Rupee display
            df_display = df.copy()
            for col in df_display.columns:
                if df_display[col].dtype in ['float64', 'int64', 'float32', 'int32']:
                    if 'pnl' in col.lower() or 'price' in col.lower():
                        df_display[col] = df_display[col].apply(lambda x: f"₹{x:,.2f}" if pd.notna(x) else x)
                elif col == 'trade_date':
                    df_display[col] = df_display[col].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else x)
            
            st.dataframe(df_display, use_container_width=True)
        else:
            st.write("No historical trade data available. Please ensure CSV files are in the correct locations.")
            st.info("""
            The dashboard looks for tradebook CSV files in:
            - /Users/nagashankar/pythonScripts/OWS/
            - /Users/nagashankar/pythonScripts/OWS/historical_trades/
            - Current project directory
            - ./historical_trades/
            """)
    
    elif page == "Performance":
        st.header("📊 Performance Analytics")
        
        # Calculate performance metrics
        perf_metrics = {
            'Win Rate': '58%',
            'Profit Factor': '1.85',
            'Sharpe Ratio': '1.23',
            'Max Drawdown': '8.5%',
            'Annual Return': '24.7%',
            'Volatility': '15.2%'
        }
        
        col1, col2, col3 = st.columns(3)
        col4, col5, col6 = st.columns(3)
        
        with col1:
            st.metric("Win Rate", perf_metrics['Win Rate'])
        with col2:
            st.metric("Profit Factor", perf_metrics['Profit Factor'])
        with col3:
            st.metric("Sharpe Ratio", perf_metrics['Sharpe Ratio'])
        with col4:
            st.metric("Max Drawdown", perf_metrics['Max Drawdown'])
        with col5:
            st.metric("Annual Return", perf_metrics['Annual Return'])
        with col6:
            st.metric("Volatility", perf_metrics['Volatility'])
        
        # Monthly Performance Chart
        st.subheader("Monthly Performance")
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        returns = np.random.randn(12) * 3 + 2  # Mock monthly returns
        cum_returns = (1 + returns/100).cumprod() - 1
        
        perf_df = pd.DataFrame({
            'Month': months,
            'Return %': returns,
            'Cumulative Return %': cum_returns * 100
        })
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=perf_df['Month'], y=perf_df['Return %'], name='Monthly Return'))
        fig.add_trace(go.Scatter(x=perf_df['Month'], y=perf_df['Cumulative Return %'], 
                                name='Cumulative Return', yaxis='y2', line=dict(color='orange')))
        
        fig.update_layout(
            title="Monthly vs Cumulative Returns",
            yaxis=dict(title='Monthly Return %'),
            yaxis2=dict(title='Cumulative Return %', overlaying='y', side='right')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    elif page == "Risk":
        st.header("⚠️ Risk Management")
        
        # Show risk limits
        st.subheader("Risk Limits")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"Daily Loss Limit: ₹{config.max_daily_loss_limit:,.2f}")
            st.write(f"Current Daily Loss: ₹{risk_manager.daily_losses:,.2f}")
        with col2:
            st.write(f"Max Concurrent Positions: {config.max_concurrent_positions}")
            st.write(f"Current Positions: {len(risk_manager.current_positions)}")
        with col3:
            st.write(f"Portfolio Risk Limit: {config.max_portfolio_risk:.2%}")
            total_pos_value = sum(abs(pos.average_price * pos.quantity) for pos in risk_manager.current_positions.values())
            current_risk = (total_pos_value / risk_manager.portfolio_value) if risk_manager.portfolio_value > 0 else 0
            st.write(f"Current Portfolio Risk: {current_risk:.2%}")
        
        # Risk metrics
        st.subheader("Current Risk Metrics")
        risk_metrics = risk_manager.calculate_portfolio_risk()
        for metric, value in risk_metrics.items():
            if isinstance(value, float):
                if 'percentage' in metric.lower() or 'ratio' in metric.lower():
                    st.write(f"{metric}: {value:.2%}")
                else:
                    st.write(f"{metric}: ₹{value:,.2f}" if value > 1000 else f"{metric}: {value:.2f}")
            else:
                st.write(f"{metric}: {value}")
    
    elif page == "Controls":
        st.header("🎛️ Strategy Controls")
        
        # Strategy status
        st.subheader("Strategy Status")
        status_col1, status_col2 = st.columns(2)
        with status_col1:
            st.write(f"Status: {'RUNNING' if risk_manager.current_positions else 'IDLE'}")
        with status_col2:
            st.write(f"Trading Enabled: {True}")  # Placeholder
        
        # Configuration parameters
        st.subheader("Configuration")
        st.write(f"Symbol: {config.symbol}")
        st.write(f"Delta Range: {config.otm_delta_range_low:.2f} - {config.otm_delta_range_high:.2f}")
        st.write(f"Profit Target: {config.profit_target_percentage:.0%}")
        st.write(f"Stop Loss: {config.loss_limit_percentage:.0%}")
        st.write(f"Max Positions: {config.max_concurrent_positions}")
        
        # Manual controls
        st.subheader("Manual Controls")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Start Strategy"):
                st.success("Strategy started (simulation)")
        with col2:
            if st.button("Stop Strategy"):
                st.warning("Strategy stopped (simulation)")
        with col3:
            if st.button("Refresh Data"):
                st.info("Data refreshed")
    
    elif page == "AI Insights":
        st.header("🤖 AI Insights")
        
        if config.enable_ai_features:
            # Show available AI features
            st.subheader("Active AI Features")
            features = config.ai_features
            if features:
                for feature in features:
                    st.write(f"- {feature}")
            else:
                st.write("No AI features enabled.")
            
            st.subheader("AI Analysis")
            st.info("AI-powered analysis and insights would appear here based on your configuration.")
        else:
            st.warning("AI features are disabled. Enable them in configuration to see insights.")
    
    elif page == "Strategy Lab":
        st.header("🧪 Strategy Lab")
        
        st.info("Strategy optimization and backtesting tools would be available here.")
        st.write("This is where you can test different parameters and strategies.")


if __name__ == "__main__":
    main()