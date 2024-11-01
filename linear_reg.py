import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from dotenv import dotenv_values
import time
config = dotenv_values(".env")
API_KEY = config["alpaca-key"]
SECRET_KEY = config["secret-key"]
BASE_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}

# Fetch tickers using Alpaca's API
def fetch_tickers(limit=20):
    try:
        response = requests.get(f"{BASE_URL}/v2/assets", headers=HEADERS)
        response.raise_for_status()
        assets = response.json()
        tickers = [asset['symbol'] for asset in assets if asset['tradable']][:limit]
        return tickers
    except Exception as e:
        print(f"Error fetching tickers: {e}")
        return []

# Fetch historical bars for a ticker
def fetch_historical_data(symbol, days=30):
    end = datetime.now().isoformat()
    try:
        response = requests.get(
            f"{DATA_URL}/v1/stocks/{symbol}/bars",
            params={
                "start": (datetime.now() - timedelta(days=days)).isoformat(),
                "end": end,
                "timeframe": "1Min",
            },
            headers=HEADERS
        )
        response.raise_for_status()
        data = response.json()['bars']
        df = pd.DataFrame(data)
        df['t'] = pd.to_datetime(df['t'], utc=True)
        df.set_index('t', inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

# Calculate the master linear regression
def get_master_linear_regression(symbol):
    eastern = pytz.timezone('US/Eastern')
    now_eastern = datetime.now(eastern)
    start_time = now_eastern.replace(hour=9, minute=30, second=0, microsecond=0)

    # Get historical data
    df = fetch_historical_data(symbol)
    if df.empty:
        print(f"No data available for {symbol}")
        return None

    # Filter for market hours
    df = df.between_time('09:30', '16:00')

    # Prepare lists for linear regression
    times_numeric = [(t - start_time).total_seconds() / 60 for t in df.index]
    prices = df['c'].tolist()
    volumes = df['v'].tolist()

    if len(times_numeric) < 2:
        print(f"Not enough data points for {symbol}")
        return None

    # Perform linear regression
    price_slope, _ = np.polyfit(times_numeric, prices, 1)
    volume_slope, _ = np.polyfit(times_numeric, volumes, 1)
    master_slope = price_slope * volume_slope

    return {
        'symbol': symbol,
        'price_slope': price_slope,
        'volume_slope': volume_slope,
        'master_slope': master_slope
    }

def main():
    tickers = fetch_tickers(limit=20)
    print(f"Fetched tickers: {tickers}")

    results = []
    for ticker in tickers:
        print(f"Processing {ticker}...")
        result = get_master_linear_regression(ticker)
        if result:
            results.append(result)

    print("\nMaster Linear Regressions:")
    for res in results:
        print(f"{res['symbol']}: Master Slope={res['master_slope']:.4f}, "
              f"Price Slope={res['price_slope']:.4f}, Volume Slope={res['volume_slope']:.4f}")

if __name__ == "__main__":
    main()
