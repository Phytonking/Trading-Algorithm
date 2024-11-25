import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import requests

# === Parameters ===
PORTFOLIO_SIZE = 5000000  # $5 million
TRANSACTION_COST = 0.01  # $0.01 per share
START_DATE = '2022-05-01'
END_DATE = '2024-11-01'
FED_API = "cc29e12bf7365d61df7f30a335e24ca1"

# === Data Download ===
def download_data(events, start_date=START_DATE, end_date=END_DATE):
    tickers = events['Ticker'].unique().tolist()
    prices = yf.download(tickers, start=start_date, end=end_date, group_by='ticker')
    spy = yf.download('SPY', start=start_date, end=end_date)
    return prices, spy

# === Filter by Index Function ===
def filter_by_index(events, index_name):
    if index_name == 'All':
        return events
    return events[events['Index Change'] == index_name]

# === Transaction Costs Calculation ===
def calculate_transaction_costs(shares):
    return shares * TRANSACTION_COST

# === Overnight Costs Calculation ===
def overnight_costs(position, fed_rate, holding_period, is_long=True):
    rate = (fed_rate / 100) + (0.015 if is_long else 0.01)
    return (position * rate * holding_period) / 365

# === Fetch Fed Funds Rate ===
def get_fed_funds_rate(date):
    endpoint = f'https://markets.newyorkfed.org/api/rates/unsecured/effr/search.json?startDate={START_DATE}&endDate={END_DATE}&type=rate'
    response = requests.get(endpoint)

    if response.status_code == 200:
        data = response.json()
        for x in data["refRates"]:
            if str(x["effectiveDate"]) == str(date).split(" ")[0]:
                return float(x["percentRate"]) + 1.25
    else:
        print("Error fetching data:", response.status_code)
        return None

# === Portfolio Allocation Based on Liquidity Constraints ===
def allocate_positions(prices, events):
    allocations = {}
    for ticker in events['Ticker'].unique():
        avg_volume = prices[ticker]['Volume'].rolling(20).mean().iloc[-1]
        max_position = avg_volume * 0.01
        allocations[ticker] = min(max_position, PORTFOLIO_SIZE / len(events))
    return allocations

# === SPY Hedge PnL Calculation ===
def calculate_hedge_pnl(trade_date, exit_date, spy, portfolio_size):
    spy_data = spy.loc[trade_date:exit_date]
    if spy_data.empty or len(spy_data) < 2:
        return 0.0

    hedge_size = portfolio_size / spy_data.iloc[0]["Open"]
    entry_price = spy_data.iloc[0]["Open"]
    exit_price = spy_data.iloc[-1]["Close"]

    hedge_pnl = hedge_size * (exit_price - entry_price)
    return hedge_pnl

# === Backtest Trading Strategies ===
def backtest(events, prices, spy):
    results = []
    fed_rate = 0
    for _, event in events.iterrows():
        ticker = event['Ticker']
        trade_date = pd.to_datetime(event["Trade Date"])
        fed_rate = get_fed_funds_rate(str(trade_date))

        max_possible_holding_period = (prices[ticker].index[-1] - trade_date).days
        if max_possible_holding_period < 1:
            continue

        holding_period = np.random.randint(1, max_possible_holding_period + 1)
        exit_date = trade_date + timedelta(days=holding_period)

        try:
            entry_price = prices[ticker].loc[trade_date]['Open']
            exit_price = prices[ticker].loc[exit_date]['Close']
        except KeyError:
            print(f"Missing data for {ticker} on {trade_date} or {exit_date}. Skipping...")
            continue

        if pd.isna(entry_price) or pd.isna(exit_price):
            continue

        shares = PORTFOLIO_SIZE // entry_price
        pnl = (exit_price - entry_price) * shares

        txn_costs = calculate_transaction_costs(shares)
        overnight_cost = overnight_costs(shares * entry_price, fed_rate, holding_period)

        # Hedge PnL
        hedge_pnl = calculate_hedge_pnl(trade_date, exit_date, spy, PORTFOLIO_SIZE)

        # Net PnL (with hedge)
        net_pnl = pnl - txn_costs - overnight_cost - hedge_pnl

        if net_pnl != 0:
            results.append({
                'Ticker': ticker,
                'Entry Date': trade_date,
                'Exit Date': exit_date,
                'Holding Period (Days)': holding_period,
                'Entry Price': entry_price,
                'Exit Price': exit_price,
                'PnL': pnl,
                'Hedge PnL': hedge_pnl,
                'Net PnL': net_pnl,
                'Transaction Costs': txn_costs
            })

    return pd.DataFrame(results)

# === Plotting the Results ===
def plot_results(results):
    daily_pnl = results.groupby("Entry Date")["Net PnL"].sum()

    # Generate Equity Curve
    equity_curve = daily_pnl.cumsum()

    plt.figure(figsize=(12, 6))
    plt.plot(equity_curve, label="Equity Curve (Momentum Strategy with Hedge)", color="blue")
    plt.title("Equity Curve with SPY Hedge")
    plt.xlabel("Date")
    plt.ylabel("Cumulative PnL ($)")
    plt.legend()
    plt.grid(True)
    plt.show()

# === Generate PnL Summary ===
def pnl_summary(results):
    total_profit = results[results['Net PnL'] > 0]['Net PnL'].sum()
    total_loss = results[results['Net PnL'] < 0]['Net PnL'].sum()
    net_pnl = results['Net PnL'].sum()
    num_winning_trades = (results['Net PnL'] > 0).sum()
    num_losing_trades = (results['Net PnL'] < 0).sum()

    summary = {
        'Total Profit': total_profit,
        'Total Loss': total_loss,
        'Net PnL': net_pnl,
        'Number of Winning Trades': num_winning_trades,
        'Number of Losing Trades': num_losing_trades
    }
    return summary

# === Plotting the Results (Comparison of Hedge vs No Hedge) ===
def plot_results_comparison(results):
    # Calculate daily PnL for both with and without hedge
    daily_pnl_with_hedge = results.groupby("Entry Date")["Net PnL"].sum()
    daily_pnl_without_hedge = results.groupby("Entry Date")["PnL"].sum()

    # Generate Equity Curves
    equity_curve_with_hedge = daily_pnl_with_hedge.cumsum()
    equity_curve_without_hedge = daily_pnl_without_hedge.cumsum()

    # Plot Equity Curves
    plt.figure(figsize=(12, 6))
    plt.plot(equity_curve_with_hedge, label="With SPY Hedge", color="blue")
    plt.plot(equity_curve_without_hedge, label="Without SPY Hedge", color="orange")
    plt.title("Equity Curve Comparison: With vs Without SPY Hedge")
    plt.xlabel("Date")
    plt.ylabel("Cumulative PnL ($)")
    plt.legend()
    plt.grid(True)
    plt.show()


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

    # Run the backtest
    results = backtest(events, prices, spy)

    # Filter out invalid or zero PnL results
    results = results[results['Net PnL'].notna() & (results['Net PnL'] != 0)]

    # Sort results by Net PnL
    results_sorted = results.sort_values(by='Net PnL', ascending=False)

    # Save sorted results to CSV
    results_sorted.to_csv('results_sorted.csv', index=False)
    print("\nSorted Results:")
    print(results_sorted)

    # Generate and print PnL summary
    summary = pnl_summary(results_sorted)
    print("\nPnL Summary:")
    for key, value in summary.items():
        print(f"{key}: {value}")

    # Plot comparison of equity curves with and without hedge
    if not results.empty:
        plot_results_comparison(results)

