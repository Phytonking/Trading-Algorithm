import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# === Parameters ===
PORTFOLIO_SIZE = 5000000  # $5 million
TRANSACTION_COST = 0.01  # $0.01 per share
START_DATE = '2022-05-01'
END_DATE = '2024-10-01'

# === Data Download ===
def download_data(events, start_date=START_DATE, end_date=END_DATE):
    tickers = events['Ticker'].unique().tolist()
    prices = yf.download(tickers, start=start_date, end=end_date, group_by='ticker')
    spy = yf.download('SPY', start=start_date, end=end_date)
    return prices, spy

# === Filter by Index Function ===
def filter_by_index(events, index_name):
    """Filter events based on the specified index or include all indexes if 'All' is selected."""
    if index_name == 'All':
        return events  # Return all events without filtering
    return events[events['Index Change'] == index_name]

# === Transaction Costs Calculation ===
def calculate_transaction_costs(shares):
    return shares * TRANSACTION_COST

# === Overnight Costs Calculation ===
def overnight_costs(position, fed_rate, holding_period, is_long=True):
    rate = fed_rate + (0.015 if is_long else 0.01)
    return (position * rate * holding_period) / 365

# === Fetch Fed Funds Rate ===
def get_fed_funds_rate():
    return 0.05  # Constant 5% Fed Funds rate

# === Portfolio Allocation Based on Liquidity Constraints ===
def allocate_positions(prices, events):
    allocations = {}
    for ticker in events['Ticker'].unique():
        avg_volume = prices[ticker]['Volume'].rolling(20).mean().iloc[-1]
        max_position = avg_volume * 0.01
        allocations[ticker] = min(max_position, PORTFOLIO_SIZE / len(events))
    return allocations

# === Backtest Trading Strategies (Supports Multiple Trades per Stock) ===
def backtest(events, prices, spy, holding_period=5):
    results = []
    fed_rate = get_fed_funds_rate()

    for _, event in events.iterrows():
        ticker = event['Ticker']
        trade_date = pd.to_datetime(event['Trade Date'])

        try:
            entry_price = prices[ticker].loc[trade_date]['Open']
            exit_price = prices[ticker].shift(-holding_period).loc[trade_date]['Close']
        except KeyError:
            print(f"Missing data for {ticker} on {trade_date}. Skipping...")
            continue

        if pd.isna(entry_price) or pd.isna(exit_price):
            continue

        shares = PORTFOLIO_SIZE // entry_price
        pnl = (exit_price - entry_price) * shares

        txn_costs = calculate_transaction_costs(shares)
        overnight_cost = overnight_costs(shares * entry_price, fed_rate, holding_period)

        net_pnl = pnl - txn_costs - overnight_cost

        if net_pnl != 0:
            results.append({
                'Ticker': ticker,
                'Entry Date': trade_date,
                'Exit Date': trade_date + timedelta(days=holding_period),
                'PnL': net_pnl,
            })

    return pd.DataFrame(results)

# === Plotting the Results ===
def plot_results(results):
    results.set_index('Exit Date')['PnL'].cumsum().plot(title='Cumulative PnL')
    plt.xlabel('Date')
    plt.ylabel('Cumulative PnL ($)')
    plt.show()

# === Generate PnL Summary ===
def pnl_summary(results):
    total_profit = results[results['PnL'] > 0]['PnL'].sum()
    total_loss = results[results['PnL'] < 0]['PnL'].sum()
    net_pnl = results['PnL'].sum()
    num_winning_trades = (results['PnL'] > 0).sum()
    num_losing_trades = (results['PnL'] < 0).sum()

    summary = {
        'Total Profit': total_profit,
        'Total Loss': total_loss,
        'Net PnL': net_pnl,
        'Number of Winning Trades': num_winning_trades,
        'Number of Losing Trades': num_losing_trades
    }
    return summary

# === Sort Results by Profit/Loss ===
def sort_results(results, by='PnL', ascending=False):
    return results.sort_values(by=by, ascending=ascending)

# === Main Execution ===
if __name__ == "__main__":
    # Load events data
    events = pd.read_csv('indexInfo.csv')

    # === Filter by Index ===
    index_name = input("Enter the index name ('S&P 400', 'S&P 500', 'S&P 600', or 'All'): ")
    events = filter_by_index(events, index_name)

    # Download price data
    prices, spy = download_data(events)

    # Allocate positions
    allocations = allocate_positions(prices, events)

    # Run the backtest (supports multiple trades per stock)
    results = backtest(events, prices, spy)

    # Filter out invalid or zero PnL results
    results = results[results['PnL'].notna() & (results['PnL'] != 0)]

    # Sort results by PnL
    results_sorted = sort_results(results, by='PnL', ascending=False)

    # Save sorted results to CSV
    results_sorted.to_csv('results_sorted.csv', index=False)
    print("\nSorted Results:")
    print(results_sorted)

    # Generate and print PnL summary
    summary = pnl_summary(results)
    print("\nPnL Summary:")
    for key, value in summary.items():
        print(f"{key}: {value}")


    """
    # Plot results if valid trades exist
    if not results_sorted.empty:
        plot_results(results)
    """
