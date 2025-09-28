"""
Prepare NIFTY Data Script for Options Wheel Strategy Trading Bot
This script provides users with a choice to generate sample data or download real NSE data
"""
import os
import sys
from pathlib import Path
import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))
from backtesting.sample_data_generator import save_sample_data
from backtesting.nse_data_collector import collect_nse_data_for_backtesting


def main():
    """
    Main function to prepare NIFTY data for backtesting
    Offers users a choice between sample data and real NSE data
    """
    print("="*60)
    print("OPTIONS WHEEL STRATEGY - DATA PREPARATION")
    print("="*60)
    print("\nThis script will help you prepare data for backtesting:")
    print("1. Generate sample data (quick start, synthetic)")
    print("2. Download real NSE data (requires internet, may take time)")
    print("3. Exit")
    print("\nNote: This is for educational purposes only")
    print("="*60)
    
    while True:
        try:
            choice = input("\nPlease select an option (1, 2, or 3): ").strip()
            
            if choice == "1":
                print("\nGenerating sample data...")
                sample_data = save_sample_data()
                
                print("\n✓ Sample data generated successfully!")
                print("Files created:")
                print("  - data/sample_nifty_data.csv")
                print("  - data/sample_options_chain.json") 
                print("  - historical_trades/sample_trades.csv")
                print("  - sample_trades.csv")
                print("\nYou can now run the backtesting with sample data.")
                break
                
            elif choice == "2":
                print("\nDownloading real NSE data...")
                print("Note: This may take several minutes depending on the date range.")
                
                # In a real implementation, we would ask for date range
                print("Using default date range of last 1 year for NIFTY data...")
                
                try:
                    nifty_data, option_data = collect_nse_data_for_backtesting()
                    
                    print(f"\n✓ Real NSE data collected successfully!")
                    print(f"  - NIFTY data: {len(nifty_data)} days")
                    print(f"  - Options chain: {len(option_data)} days")
                    print("Files saved in the 'data' directory.")
                    break
                except Exception as e:
                    print(f"\n❌ Error collecting NSE data: {e}")
                    print("Falling back to sample data generation...")
                    
                    # Generate sample data if NSE collection fails
                    sample_data = save_sample_data()
                    print("\n✓ Sample data generated successfully!")
                    break
            
            elif choice == "3":
                print("\nExiting without generating data.")
                sys.exit(0)
                
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n\nProcess interrupted by user. Exiting...")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            retry = input("Would you like to try again? (y/n): ").strip().lower()
            if retry != 'y':
                sys.exit(1)
    
    print("\n" + "="*60)
    print("DATA PREPARATION COMPLETED")
    print("You can now proceed with backtesting or running the strategy.")
    print("="*60)


if __name__ == "__main__":
    main()