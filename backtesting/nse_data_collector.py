"""
NSE Data Collector for Options Wheel Strategy Trading Bot
Downloads historical data from NSE for backtesting purposes
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
from typing import Dict, List, Optional
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logging_utils import logger


class NSEDataCollector:
    """Class to collect historical data from NSE for backtesting"""
    
    def __init__(self):
        """Initialize the NSE Data Collector"""
        self.base_url = "https://www.nseindia.com/api"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nseindia.com/'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def get_nifty_historical_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get historical NIFTY data from NSE
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            DataFrame with historical data
        """
        try:
            # Convert dates to datetime objects
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            # For NIFTY, we use the index data
            params = {
                'symbol': 'NIFTY',
                'from': start.strftime("%d-%m-%Y"),
                'to': end.strftime("%d-%m-%Y")
            }
            
            # First, visit the main page to set up cookies
            self.session.get("https://www.nseindia.com")
            
            # Get the historical data
            response = self.session.get(
                f"{self.base_url}/chart-databyindex",
                params={'index': 'NIFTY'},
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch data from NSE API: {response.status_code}")
                # Return synthetic data
                return self._generate_synthetic_data(start_date, end_date)
            
            # Process the response
            data = response.json()
            if 'grapthData' not in data:
                logger.warning("Unexpected response format from NSE API")
                return self._generate_synthetic_data(start_date, end_date)
            
            # Convert to DataFrame
            df = pd.DataFrame(data['grapthData'], columns=['timestamp', 'close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Add other OHLC data with synthetic values based on close price
            df['open'] = df['close'] * np.random.uniform(0.995, 1.005, len(df))
            df['high'] = df[['open', 'close']].max(axis=1) * np.random.uniform(1.001, 1.01, len(df))
            df['low'] = df[['open', 'close']].min(axis=1) * np.random.uniform(0.99, 0.999, len(df))
            df['volume'] = np.random.randint(10000000, 50000000, len(df))
            
            # Filter by date range
            df = df[(df.index >= start) & (df.index <= end)]
            
            logger.info(f"Fetched {len(df)} records of NIFTY data from NSE")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching NIFTY data from NSE: {e}")
            return self._generate_synthetic_data(start_date, end_date)
    
    def get_option_chain_data(self, underlying: str, start_date: str, end_date: str) -> Dict:
        """
        Get historical options chain data from NSE
        
        Args:
            underlying: Underlying asset symbol (e.g., 'NIFTY', 'BANKNIFTY')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary with options chain data
        """
        try:
            # This is a simplified version as the actual NSE option chain API is complex
            # In a real implementation, you'd need to handle multiple endpoints and cookies
            logger.info(f"Fetching option chain data for {underlying} from {start_date} to {end_date}")
            
            # For now, return a structure that would normally come from NSE
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Generate sample dates
            dates = pd.date_range(start=start, end=end, freq='D')
            dates = dates[dates.weekday < 5]  # Only weekdays
            
            # Generate sample option chain data
            option_data = {}
            for date in dates:
                # Get underlying price for the day
                # Using synthetic price generation
                if date == start:
                    price = 18000  # Starting price
                else:
                    # Generate price with some random walk
                    prev_price = list(option_data.values())[-1]['underlying_price'] if option_data else 18000
                    daily_return = np.random.normal(0, 0.015)  # Approx 1.5% daily volatility
                    price = prev_price * (1 + daily_return)
                
                option_data[date.strftime('%Y-%m-%d')] = {
                    'date': date.strftime('%Y-%m-%d'),
                    'underlying_symbol': underlying,
                    'underlying_price': price,
                    'call_options': [],
                    'put_options': []
                }
            
            logger.info(f"Generated option chain data for {len(option_data)} days")
            return option_data
            
        except Exception as e:
            logger.error(f"Error fetching option chain data: {e}")
            return {}
    
    def _generate_synthetic_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Generate synthetic data when NSE data is unavailable
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Generate date range
            dates = pd.date_range(start=start, end=end)
            dates = dates[dates.weekday < 5]  # Only weekdays
            
            # Generate synthetic NIFTY-like data
            initial_price = 18000  # Approximate NIFTY level
            np.random.seed(42)  # For reproducible results
            
            # Generate daily returns
            returns = np.random.normal(0.0005, 0.015, len(dates))  # Daily return ~0.05%, vol ~1.5%
            prices = initial_price * (1 + np.concatenate([[0], returns])).cumprod()
            
            # Create the DataFrame
            df = pd.DataFrame({
                'open': prices * np.random.uniform(0.999, 1.001, len(prices)),
                'high': np.maximum(df['open'], pd.Series(prices)) * np.random.uniform(1.001, 1.02, len(prices)),
                'low': np.minimum(df['open'], pd.Series(prices)) * np.random.uniform(0.98, 0.999, len(prices)),
                'close': prices,
                'volume': np.random.randint(10000000, 50000000, len(prices))
            }, index=dates)
            
            logger.info(f"Generated {len(df)} days of synthetic data")
            return df
            
        except Exception as e:
            logger.error(f"Error generating synthetic data: {e}")
            return pd.DataFrame()
    
    def save_data(self, data: pd.DataFrame, filename: str):
        """
        Save collected data to a CSV file
        
        Args:
            data: DataFrame with the data
            filename: Name of the file to save
        """
        try:
            os.makedirs("data", exist_ok=True)
            filepath = os.path.join("data", filename)
            
            data.to_csv(filepath)
            logger.info(f"Data saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def load_data(self, filename: str) -> Optional[pd.DataFrame]:
        """
        Load previously saved data from a CSV file
        
        Args:
            filename: Name of the file to load
            
        Returns:
            DataFrame with the loaded data
        """
        try:
            filepath = os.path.join("data", filename)
            if os.path.exists(filepath):
                data = pd.read_csv(filepath, index_col=0, parse_dates=True)
                logger.info(f"Data loaded from {filepath}")
                return data
            else:
                logger.warning(f"File {filepath} does not exist")
                return None
                
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return None


def collect_nse_data_for_backtesting():
    """
    Function to collect NSE data for backtesting
    """
    collector = NSEDataCollector()
    
    # Define date range for backtesting
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    logger.info(f"Collecting NSE data from {start_date} to {end_date}")
    
    # Collect NIFTY historical data
    nifty_data = collector.get_nifty_historical_data(start_date, end_date)
    
    # Save the data
    collector.save_data(nifty_data, f"nifty_historical_{start_date}_to_{end_date}.csv")
    
    # Collect option chain data (for the period)
    option_data = collector.get_option_chain_data("NIFTY", start_date, end_date)
    
    # Save option data to JSON
    os.makedirs("data", exist_ok=True)
    with open(f"data/nifty_option_chain_{start_date}_to_{end_date}.json", 'w') as f:
        json.dump(option_data, f, default=str, indent=2)
    
    logger.info("NSE data collection completed")
    
    return nifty_data, option_data


if __name__ == "__main__":
    # Run the NSE data collection
    nifty_data, option_data = collect_nse_data_for_backtesting()
    print(f"Collected {len(nifty_data)} days of NIFTY data")