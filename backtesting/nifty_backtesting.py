"""
NIFTY backtesting module for Options Wheel Strategy Trading Bot
Implements comprehensive backtesting with realistic market conditions
"""
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
try:
    import yfinance as yf
except ImportError:
    yf = None
    print("yfinance not available, using synthetic data only")
from typing import Dict, List, Optional, Tuple
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os

# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.strategy import OptionWheelStrategy
from config.config import config
from models.models import Trade, Position, OptionContract
from models.enums import TransactionType, ProductType, OrderType
from utils.logging_utils import logger
from backtesting.mock_kite import MockKiteConnect


class NiftyBacktestingStrategy:
    """Backtesting strategy for the Option Wheel Strategy using NIFTY data"""
    
    def __init__(self):
        """Initialize backtesting with historical data"""
        self.mock_kite = MockKiteConnect(initial_balance=100000)  # Starting with 1L INR
        self.strategy = OptionWheelStrategy(kite_client=self.mock_kite)
        self.historical_data = {}
        self.start_date = None
        self.end_date = None
        self.current_date = None
        self.results = {
            'trades': [],
            'daily_pnl': [],
            'equity_curve': [],
            'transactions': [],
            'total_return': 0.0,
            'annualized_return': 0.0,
            'volatility': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0
        }
    
    def load_nifty_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Load NIFTY historical data for backtesting
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            DataFrame with historical NIFTY data
        """
        try:
            logger.info(f"Loading NIFTY data from {start_date} to {end_date}")
            
            # Using yfinance to get NIFTY data (alternative source)
            # Since NIFTY might not be available directly on yfinance, we'll use a surrogate
            if yf is not None:
                nifty_data = yf.download("^NSEI", start=start_date, end=end_date, interval="1d")
                
                # If NIFTY isn't available, create synthetic data
                if nifty_data.empty:
                    logger.warning("NIFTY data not available from yfinance, creating synthetic data")
                    dates = pd.date_range(start=start_date, end=end_date)
                    np.random.seed(42)
                    
                    # Generate synthetic NIFTY-like data
                    initial_price = 18000  # Approximate NIFTY level
                    returns = np.random.normal(0.0005, 0.015, len(dates))  # Daily return ~0.05%, vol ~1.5%
                    prices = initial_price * (1 + np.concatenate([[0], returns])).cumprod()
                    
                    nifty_data = pd.DataFrame({
                        'Open': prices,
                        'High': prices * np.random.uniform(1.001, 1.02, len(prices)),
                        'Low': prices * np.random.uniform(0.98, 0.999, len(prices)),
                        'Close': prices,
                        'Volume': np.random.randint(10000000, 50000000, len(prices))
                    }, index=dates)
            else:
                # yfinance not available, create synthetic data
                logger.warning("yfinance not available, creating synthetic data")
                dates = pd.date_range(start=start_date, end=end_date)
                np.random.seed(42)
                
                # Generate synthetic NIFTY-like data
                initial_price = 18000  # Approximate NIFTY level
                returns = np.random.normal(0.0005, 0.015, len(dates))  # Daily return ~0.05%, vol ~1.5%
                prices = initial_price * (1 + np.concatenate([[0], returns])).cumprod()
                
                nifty_data = pd.DataFrame({
                    'Open': prices,
                    'High': prices * np.random.uniform(1.001, 1.02, len(prices)),
                    'Low': prices * np.random.uniform(0.98, 0.999, len(prices)),
                    'Close': prices,
                    'Volume': np.random.randint(10000000, 50000000, len(prices))
                }, index=dates)
            
            # Ensure all values are numeric and handle missing data
            nifty_data = nifty_data.select_dtypes(include=[np.number]).fillna(method='ffill')
            
            logger.info(f"Loaded {len(nifty_data)} days of NIFTY data")
            return nifty_data
            
        except Exception as e:
            logger.error(f"Error loading NIFTY data: {e}")
            # Create minimal synthetic data to continue
            dates = pd.date_range(start=start_date, end=end_date)
            initial_price = 18000
            prices = [initial_price]
            
            for i in range(1, len(dates)):
                # Generate random price movement
                change = np.random.normal(0, 0.015)  # 1.5% daily volatility
                new_price = prices[-1] * (1 + change)
                prices.append(new_price)
            
            nifty_data = pd.DataFrame({
                'Open': prices,
                'High': [p * np.random.uniform(1.001, 1.01) for p in prices],
                'Low': [p * np.random.uniform(0.99, 0.999) for p in prices],
                'Close': prices,
                'Volume': [np.random.randint(10000000, 50000000) for _ in prices]
            }, index=dates)
            
            logger.info("Created synthetic NIFTY data")
            return nifty_data
    
    def generate_options_chain(self, nifty_price: float, expiry_date: datetime) -> List[OptionContract]:
        """
        Generate synthetic options chain based on NIFTY price
        
        Args:
            nifty_price: Current NIFTY price
            expiry_date: Options expiry date
            
        Returns:
            List of OptionContract objects
        """
        try:
            contracts = []
            
            # Generate strikes around current price (ATM, ITM, OTM)
            at_the_money_strike = round(nifty_price / 100) * 100  # Round to nearest 100
            strikes = list(range(int(at_the_money_strike - 800), int(at_the_money_strike + 800), 100))
            
            # Generate call and put options for each strike
            for i, strike in enumerate(strikes):
                # Calculate approximate premium based on moneyness
                if strike <= nifty_price:  # ITM calls or OTM puts
                    call_premium = max(0, nifty_price - strike) + np.random.uniform(50, 150)
                    put_premium = max(0, strike - nifty_price) + np.random.uniform(20, 80)
                else:  # OTM calls or ITM puts
                    call_premium = max(0, strike - nifty_price) + np.random.uniform(20, 80)
                    put_premium = max(0, nifty_price - strike) + np.random.uniform(50, 150)
                
                # Add some randomness
                call_premium *= np.random.uniform(0.8, 1.2)
                put_premium *= np.random.uniform(0.8, 1.2)
                
                # Calculate approximate delta
                call_delta = max(0.05, min(0.95, (nifty_price - strike + 500) / 1000)) if strike <= nifty_price else max(0.05, min(0.95, (strike - nifty_price) / 1000))
                put_delta = -max(0.05, min(0.95, (strike - nifty_price) / 1000)) if strike >= nifty_price else -max(0.05, min(0.95, (nifty_price - strike) / 1000))
                
                # Create call option
                call_contract = OptionContract(
                    symbol=f"NIFTY{expiry_date.strftime('%y%b').upper()}{strike}CE",
                    instrument_token=100000 + i * 2,
                    exchange="NFO",
                    last_price=call_premium,
                    expiry=expiry_date,
                    strike=strike,
                    tick_size=0.05,
                    lot_size=50,
                    instrument_type="CE",
                    segment="NFO-OPT",
                    option_type="CE",
                    tradingsymbol=f"NIFTY{expiry_date.strftime('%y%b').upper()}{strike}CE",
                    delta=call_delta,
                    gamma=np.random.uniform(0.001, 0.003),
                    theta=np.random.uniform(-0.5, -0.1),
                    vega=np.random.uniform(8, 12),
                    implied_volatility=np.random.uniform(0.15, 0.35),
                    open_interest=np.random.randint(10000, 100000)
                )
                
                # Create put option
                put_contract = OptionContract(
                    symbol=f"NIFTY{expiry_date.strftime('%y%b').upper()}{strike}PE",
                    instrument_token=100001 + i * 2,
                    exchange="NFO",
                    last_price=put_premium,
                    expiry=expiry_date,
                    strike=strike,
                    tick_size=0.05,
                    lot_size=50,
                    instrument_type="PE",
                    segment="NFO-OPT",
                    option_type="PE",
                    tradingsymbol=f"NIFTY{expiry_date.strftime('%y%b').upper()}{strike}PE",
                    delta=put_delta,
                    gamma=np.random.uniform(0.001, 0.003),
                    theta=np.random.uniform(-0.5, -0.1),
                    vega=np.random.uniform(8, 12),
                    implied_volatility=np.random.uniform(0.15, 0.35),
                    open_interest=np.random.randint(10000, 100000)
                )
                
                contracts.extend([call_contract, put_contract])
            
            return contracts
            
        except Exception as e:
            logger.error(f"Error generating options chain: {e}")
            return []
    
    def simulate_strategy(self, start_date: str, end_date: str, save_results: bool = True) -> Dict[str, any]:
        """
        Run the backtesting simulation
        
        Args:
            start_date: Start date for backtesting
            end_date: End date for backtesting
            save_results: Whether to save results to file
            
        Returns:
            Dictionary with backtesting results
        """
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.current_date = self.start_date
        
        logger.info(f"Starting backtesting from {start_date} to {end_date}")
        
        # Load historical data
        nifty_data = self.load_nifty_data(start_date, end_date)
        
        # Initialize results tracking
        daily_balances = []
        all_trades = []
        transaction_log = []
        
        # Main backtesting loop
        for date, row in nifty_data.iterrows():
            # Skip weekends
            if date.weekday() > 4:
                continue
                
            # Update mock kite timestamp
            self.mock_kite.set_current_timestamp(date)
            
            # Update the price in mock kite for NIFTY
            data_for_kite = pd.DataFrame({
                'open': [row['Open']],
                'high': [row['High']], 
                'low': [row['Low']],
                'close': [row['Close']]
            }, index=[date])
            
            # Set NIFTY data in mock kite
            self.mock_kite.set_historical_data("NFO:NIFTY", data_for_kite)
            
            # Generate options chain for near-term expiry (1-2 weeks out)
            expiry_date = date + timedelta(days=7 + (date.weekday() - 0) % 7)  # Next weekly expiry
            options_chain = self.generate_options_chain(row['Close'], expiry_date)
            
            # Store options chain for this date
            self.historical_data[date] = options_chain
            
            # Execute strategy cycle
            try:
                # For backtesting, we'll implement a simplified version of the strategy
                # that uses the historical data to simulate trading decisions
                self.execute_backtesting_cycle(date, row, options_chain)
                
                # Log daily balance
                margins = self.mock_kite.margins()
                daily_balance = margins['equity']['net']
                daily_balances.append({
                    'date': date,
                    'balance': daily_balance,
                    'nifty_close': row['Close']
                })
                
                logger.debug(f"Processed {date.strftime('%Y-%m-%d')}, Balance: ₹{daily_balance:,.2f}")
                
            except Exception as e:
                logger.error(f"Error processing date {date}: {e}")
                continue
        
        # Calculate performance metrics
        self.calculate_performance_metrics(daily_balances, self.mock_kite.trades)
        
        # Save results if requested
        if save_results:
            self.save_results()
        
        logger.info("Backtesting completed")
        return self.results
    
    def execute_backtesting_cycle(self, current_date: datetime, nifty_row: pd.Series, options_chain: List[OptionContract]):
        """
        Execute a single strategy cycle in backtesting mode
        """
        # Simplified implementation focusing on the core logic
        try:
            # Find the best OTM strikes based on delta range
            nifty_price = nifty_row['Close']
            
            # Filter for appropriate delta range based on strategy mode
            if config.strategy_mode == 'conservative':
                delta_low, delta_high = 0.10, 0.15
            elif config.strategy_mode == 'aggressive':
                delta_low, delta_high = 0.25, 0.35
            else:  # balanced
                delta_low, delta_high = config.otm_delta_range_low, config.otm_delta_range_high
            
            # Filter options based on our criteria
            suitable_options = []
            for option in options_chain:
                # Check if delta is in range (absolute value for puts)
                option_delta = abs(option.delta) if option.delta else 0
                
                if not option.delta or option_delta < delta_low or option_delta > delta_high:
                    continue
                
                # Check if open interest meets minimum requirement
                if option.open_interest < config.min_open_interest:
                    continue
                
                # Only consider options on NIFTY
                if "NIFTY" in option.symbol:
                    suitable_options.append(option)
            
            # If we have suitable options and we don't have max positions yet
            if (suitable_options and 
                len(self.mock_kite.positions) < config.max_concurrent_positions):
                
                # Sort by delta (closest to target) and open interest
                best_option = min(
                    suitable_options,
                    key=lambda x: (
                        abs(abs(x.delta) - (delta_low + delta_high) / 2),
                        -x.open_interest
                    )
                )
                
                # Calculate position size based on risk management
                max_position_value = (self.mock_kite.current_balance * config.risk_per_trade_percent)
                max_quantity = int(max_position_value / (best_option.last_price * config.quantity_per_lot))
                
                # Ensure minimum lot size
                lots = max(1, min(max_quantity // config.quantity_per_lot, 1))  # Limit to 1 lot for this example
                quantity = lots * config.quantity_per_lot
                
                if quantity > 0:
                    # Place order to sell the option (collecting premium)
                    # Use MARKET order for backtesting to ensure execution
                    order_id = self.mock_kite.place_order(
                        variety=self.mock_kite.VARIETY_REGULAR,
                        exchange="NFO",
                        tradingsymbol=best_option.symbol,
                        transaction_type=TransactionType.SELL.value,
                        quantity=quantity,
                        product=ProductType.NRML.value,
                        order_type=OrderType.MARKET.value
                    )
                    
                    logger.info(f"Backtest order placed: SELL {quantity} {best_option.symbol} @ ₹{best_option.last_price}")
        
        except Exception as e:
            logger.error(f"Error in backtesting cycle: {e}")
    
    def calculate_performance_metrics(self, daily_balances: List[Dict], all_trades: List[Dict]):
        """
        Calculate performance metrics from backtesting results
        """
        try:
            if not daily_balances:
                logger.warning("No daily balances available for metrics calculation")
                return
            
            # Convert to DataFrame
            df_daily = pd.DataFrame(daily_balances)
            df_daily = df_daily.sort_values('date')
            
            # Calculate daily returns
            df_daily['daily_return'] = df_daily['balance'].pct_change()
            
            # Calculate metrics
            initial_balance = df_daily.iloc[0]['balance']
            final_balance = df_daily.iloc[-1]['balance']
            total_return = ((final_balance - initial_balance) / initial_balance) * 100
            
            # Annualized return (assuming 252 trading days in India)
            trading_days = len(df_daily)
            years = trading_days / 252
            annualized_return = (final_balance / initial_balance) ** (1/years) - 1
            
            # Volatility (standard deviation of daily returns)
            volatility = df_daily['daily_return'].std() * np.sqrt(252) * 100
            
            # Sharpe ratio (assuming risk-free rate of 6% annually)
            risk_free_rate = 0.06
            sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility != 0 else 0
            
            # Max drawdown
            df_daily['rolling_max'] = df_daily['balance'].expanding().max()
            df_daily['drawdown'] = (df_daily['balance'] - df_daily['rolling_max']) / df_daily['rolling_max']
            max_drawdown = df_daily['drawdown'].min() * 100
            
            # Win rate and profit factor from trades
            if all_trades:
                df_trades = pd.DataFrame(all_trades)
                df_trades['pnl'] = df_trades['value']  # Use value as P&L
                
                winning_trades = df_trades[df_trades['value'] > 0]
                losing_trades = df_trades[df_trades['value'] < 0]
                
                win_rate = len(winning_trades) / len(df_trades) if len(df_trades) > 0 else 0
                profit_factor = (winning_trades['value'].sum() / abs(losing_trades['value'].sum())) if abs(losing_trades['value'].sum()) > 0 else float('inf')
            else:
                win_rate = 0
                profit_factor = 0
            
            # Update results dictionary
            self.results = {
                'initial_balance': initial_balance,
                'final_balance': final_balance,
                'total_return_percent': total_return,
                'annualized_return': annualized_return * 100,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'trading_days': trading_days,
                'total_trades': len(all_trades),
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'daily_balances': df_daily.to_dict('records'),
                'all_trades': all_trades
            }
            
            logger.info(f"Performance Metrics:\n"
                       f"Total Return: {total_return:.2f}%\n"
                       f"Annualized Return: {annualized_return*100:.2f}%\n"
                       f"Volatility: {volatility:.2f}%\n"
                       f"Sharpe Ratio: {sharpe_ratio:.2f}\n"
                       f"Max Drawdown: {max_drawdown:.2f}%\n"
                       f"Win Rate: {win_rate:.2f}\n"
                       f"Profit Factor: {profit_factor:.2f}")
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
    
    def save_results(self, filename: str = "backtesting_results.json"):
        """
        Save backtesting results to a file
        
        Args:
            filename: Name of the file to save results
        """
        import json
        
        try:
            # Create results directory if it doesn't exist
            os.makedirs("results", exist_ok=True)
            filepath = os.path.join("results", filename)
            
            # Prepare results data for JSON serialization
            results_to_save = {}
            for key, value in self.results.items():
                if isinstance(value, pd.DataFrame):
                    results_to_save[key] = value.to_dict('records')
                elif isinstance(value, np.ndarray):
                    results_to_save[key] = value.tolist()
                else:
                    results_to_save[key] = value
            
            # Save to JSON file
            with open(filepath, 'w') as f:
                json.dump(results_to_save, f, default=str, indent=2)
            
            logger.info(f"Backtesting results saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving backtesting results: {e}")
    
    def print_summary(self):
        """Print a summary of backtesting results"""
        if not self.results:
            print("No backtesting results available. Run simulation first.")
            return
        
        print("\n" + "="*60)
        print("BACKTESTING RESULTS SUMMARY")
        print("="*60)
        print(f"Total Return:         {self.results['total_return_percent']:.2f}%")
        print(f"Annualized Return:    {self.results['annualized_return']:.2f}%")
        print(f"Volatility:           {self.results['volatility']:.2f}%")
        print(f"Sharpe Ratio:         {self.results['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:         {self.results['max_drawdown']:.2f}%")
        print(f"Trading Days:         {self.results['trading_days']}")
        print(f"Total Trades:         {self.results['total_trades']}")
        print(f"Win Rate:             {self.results['win_rate']:.2%}")
        print(f"Profit Factor:        {self.results['profit_factor']:.2f}")
        print(f"Initial Balance:      ₹{self.results['initial_balance']:,.2f}")
        print(f"Final Balance:        ₹{self.results['final_balance']:,.2f}")
        print("="*60)


# Example usage and testing
def run_nifty_backtest():
    """Function to run a sample backtest"""
    backtester = NiftyBacktestingStrategy()
    
    # Define date range for backtesting
    start_date = "2023-01-01"
    end_date = "2023-03-01"
    
    # Run the backtest
    results = backtester.simulate_strategy(start_date, end_date)
    
    # Print summary
    backtester.print_summary()
    
    return backtester


if __name__ == "__main__":
    # Run a sample backtest
    backtester = run_nifty_backtest()