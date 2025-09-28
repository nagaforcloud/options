"""
Sample Data Generator for Options Wheel Strategy Trading Bot
Creates realistic sample data for quick testing and backtesting
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logging_utils import logger


def generate_sample_nifty_data(
    start_date: str = "2023-01-01", 
    end_date: str = "2023-12-31",
    initial_price: float = 18000,
    volatility: float = 0.015
) -> pd.DataFrame:
    """
    Generate sample NIFTY data for backtesting
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        initial_price: Initial price of the index
        volatility: Daily volatility (standard deviation of returns)
        
    Returns:
        DataFrame with sample NIFTY data
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Generate date range (only weekdays)
    dates = pd.date_range(start=start, end=end)
    dates = dates[dates.weekday < 5]  # Only weekdays
    
    # Generate daily returns
    np.random.seed(42)  # For reproducible results
    daily_returns = np.random.normal(0.0005, volatility, len(dates))  # Daily return ~0.05%, vol ~1.5%
    
    # Calculate prices
    prices = [initial_price]
    for i in range(1, len(daily_returns)):
        new_price = prices[-1] * (1 + daily_returns[i])
        prices.append(new_price)
    
    # Generate OHLC data
    opens = [prices[0]]
    highs = []
    lows = []
    
    for i in range(1, len(prices)):
        # Generate opening prices (close of previous day with small variation)
        prev_close = prices[i-1]
        open_price = prev_close * np.random.uniform(0.999, 1.001)
        opens.append(open_price)
        
        # Generate high and low based on open and close
        high_price = max(open_price, prices[i]) * np.random.uniform(1.001, 1.02)
        low_price = min(open_price, prices[i]) * np.random.uniform(0.98, 0.999)
        
        highs.append(high_price)
        lows.append(low_price)
    
    highs = [prices[0] * np.random.uniform(1.001, 1.02)] + highs
    lows = [prices[0] * np.random.uniform(0.98, 0.999)] + lows
    
    # Generate volume data
    volumes = np.random.randint(15000000, 45000000, len(dates))
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': prices,
        'volume': volumes
    })
    
    df.set_index('date', inplace=True)
    
    logger.info(f"Generated {len(df)} days of sample NIFTY data from {start_date} to {end_date}")
    return df


def generate_sample_options_chain(
    nifty_data: pd.DataFrame,
    expiry_days: int = 30
) -> dict:
    """
    Generate sample options chain data based on NIFTY price data
    
    Args:
        nifty_data: DataFrame with NIFTY data
        expiry_days: Days to expiry for options
        
    Returns:
        Dictionary with options chain data for each date
    """
    options_chain_data = {}
    
    for date, row in nifty_data.iterrows():
        nifty_price = row['close']
        
        # Determine ATM strike (round to nearest 50)
        atm_strike = round(nifty_price / 50) * 50
        
        # Generate strikes around ATM
        strikes = list(range(int(atm_strike - 800), int(atm_strike + 800), 50))
        
        # Generate call and put options for each strike
        call_options = []
        put_options = []
        
        # Calculate expiry date
        expiry_date = date + timedelta(days=expiry_days)
        
        for strike in strikes:
            # Calculate moneyness
            moneyness_call = nifty_price / strike
            moneyness_put = strike / nifty_price
            
            # Calculate approximate premiums based on moneyness
            if moneyness_call > 1:  # ITM Call
                call_premium = (nifty_price - strike) * np.random.uniform(1.1, 1.3) + np.random.uniform(20, 50)
            else:  # OTM Call
                call_premium = (strike - nifty_price) * np.random.uniform(0.1, 0.5) + np.random.uniform(10, 30)
            
            if moneyness_put > 1:  # ITM Put
                put_premium = (strike - nifty_price) * np.random.uniform(1.1, 1.3) + np.random.uniform(20, 50)
            else:  # OTM Put
                put_premium = (nifty_price - strike) * np.random.uniform(0.1, 0.5) + np.random.uniform(10, 30)
            
            # Ensure positive premiums
            call_premium = max(5, call_premium * np.random.uniform(0.8, 1.2))
            put_premium = max(5, put_premium * np.random.uniform(0.8, 1.2))
            
            # Calculate approximate deltas
            call_delta = 1 / (1 + np.exp(-(moneyness_call - 1) * 10))  # Sigmoid function for delta
            put_delta = call_delta - 1  # Put delta = Call delta - 1
            
            # Add to lists
            call_options.append({
                'strike': strike,
                'symbol': f"NIFTY{expiry_date.strftime('%y%b').upper()}{strike}CE",
                'last_price': call_premium,
                'delta': call_delta,
                'open_interest': np.random.randint(10000, 100000),
                'volume': np.random.randint(5000, 50000)
            })
            
            put_options.append({
                'strike': strike,
                'symbol': f"NIFTY{expiry_date.strftime('%y%b').upper()}{strike}PE",
                'last_price': put_premium,
                'delta': put_delta,
                'open_interest': np.random.randint(10000, 100000),
                'volume': np.random.randint(5000, 50000)
            })
        
        options_chain_data[date.strftime('%Y-%m-%d')] = {
            'date': date.strftime('%Y-%m-%d'),
            'underlying_price': nifty_price,
            'underlying_symbol': 'NIFTY',
            'call_options': call_options,
            'put_options': put_options,
            'expiry_date': expiry_date.strftime('%Y-%m-%d')
        }
    
    logger.info(f"Generated sample options chain data for {len(options_chain_data)} days")
    return options_chain_data


def generate_sample_trade_data(
    nifty_data: pd.DataFrame,
    num_trades: int = 100
) -> pd.DataFrame:
    """
    Generate sample trade data for testing
    
    Args:
        nifty_data: DataFrame with NIFTY data
        num_trades: Number of trades to generate
        
    Returns:
        DataFrame with sample trade data
    """
    dates = np.random.choice(nifty_data.index, size=num_trades, replace=True)
    dates.sort()
    
    # Generate trade data
    symbols = [f"NIFTY{date.strftime('%y%b').upper()}{int(nifty_data.loc[date, 'close']):.0f}{'CE' if i % 2 == 0 else 'PE'}" 
               for i, date in enumerate(dates)]
    transaction_types = np.random.choice(['BUY', 'SELL'], size=num_trades) 
    
    # Calculate prices based on underlying (with some variation)
    prices = []
    for date in dates:
        base_price = nifty_data.loc[date, 'close'] / 20  # Approximate option price
        variation = np.random.uniform(0.5, 1.5)
        price = max(5, base_price * variation)  # Ensure minimum price
        prices.append(price)
    
    quantities = np.random.choice([50, 100, 150, 200], size=num_trades)
    
    # Calculate P&L randomly (some positive, some negative)
    pnl_values = np.random.normal(0, 1000, num_trades)  # Average P&L around 0 with std of 1000
    
    df = pd.DataFrame({
        'date': dates,
        'symbol': symbols,
        'transaction_type': transaction_types,
        'price': prices,
        'quantity': quantities,
        'pnl': pnl_values,
        'entry_price': prices,
        'exit_price': [p + pnl for p, pnl in zip(prices, pnl_values)] if all(tt == 'SELL' for tt in transaction_types) else prices
    })
    
    logger.info(f"Generated {len(df)} sample trades")
    return df


def save_sample_data():
    """
    Generate and save sample data to files for testing and backtesting
    """
    logger.info("Generating sample data for testing and backtesting...")
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("historical_trades", exist_ok=True)
    
    # Generate NIFTY sample data
    nifty_data = generate_sample_nifty_data(
        start_date="2023-01-01", 
        end_date="2023-06-30",
        initial_price=18000,
        volatility=0.012
    )
    
    # Save NIFTY data
    nifty_data.to_csv("data/sample_nifty_data.csv")
    logger.info("Saved sample NIFTY data to data/sample_nifty_data.csv")
    
    # Generate options chain data
    options_chain_data = generate_sample_options_chain(nifty_data, expiry_days=30)
    
    # Save options chain data
    import json
    with open("data/sample_options_chain.json", "w") as f:
        json.dump(options_chain_data, f, default=str, indent=2)
    logger.info("Saved sample options chain data to data/sample_options_chain.json")
    
    # Generate sample trade data
    trade_data = generate_sample_trade_data(nifty_data, num_trades=200)
    
    # Save trade data to CSV
    trade_data.to_csv("historical_trades/sample_trades.csv", index=False)
    logger.info("Saved sample trade data to historical_trades/sample_trades.csv")
    
    # Also save to main directory for dashboard access
    trade_data.to_csv("sample_trades.csv", index=False)
    logger.info("Saved sample trade data to sample_trades.csv")
    
    print("\nSample Data Generated Successfully!")
    print(f"NIFTY data: {len(nifty_data)} rows")
    print(f"Options chain: {len(options_chain_data)} days of data")
    print(f"Trade data: {len(trade_data)} trades")
    
    return {
        'nifty_data': nifty_data,
        'options_chain': options_chain_data,
        'trade_data': trade_data
    }


if __name__ == "__main__":
    # Generate and save sample data
    sample_data = save_sample_data()
    print("\nSample data generation completed!")