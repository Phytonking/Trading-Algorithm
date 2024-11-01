import alpaca_trade_api as tradeapi
import threading
import time
import bars
import liquidate
from market_open import marketOpen
from submit_order import *
from dotenv import dotenv_values
from account import *
from find_stocks import find_stocks
# Replace with your Alpaca API credentials
config = dotenv_values(".env")
API_KEY = config["alpaca-key"]
API_SECRET = config["secret-key"]
BASE_URL = 'https://paper-api.alpaca.markets'  # Use 'https://api.alpaca.markets' for live trading

# Initialize Alpaca API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

# Define the list of stock symbols and order size
symbols = []

order_size_in_dollars = round((float(get_cash())/len(symbols)),2)  # Number of shares per trade
profit_target = 0.001  # 0.1% profit target per trade
loss_cutoff = 0.0005  # 0.1% loss cutoff per trade

# Function to execute the trade for a single stock symbol
def scalp_trade(symbol):
    try:
        if marketOpen():
            while True:
                # Get the latest price data
                barset = bars.get_bars(symbol, "1Min", limit=1)
                current_price = barset["quote"]["bp"]
                # Place a buy order
                buy_order = send_order(
                    symbol=symbol,
                    qty=order_size_in_dollars,
                    side='buy',
                    type='market',
                    time_in_force='gtc'
                )
                print(f"Bought ${order_size_in_dollars} of {symbol} at {current_price}")

                # Monitor the position for profit or loss target
                while True:
                    barset = bars.get_bars(symbol, "1Min", limit=1)
                    new_price = barset["quote"]["bp"]

                    # Check for profit target
                    if new_price >= current_price * (1 + profit_target):
                        send_order(
                            symbol=symbol,
                            qty=order_size_in_dollars,
                            side='sell',
                            type='market',
                            time_in_force='gtc'
                        )
                        print(f"Sold ${order_size_in_dollars} of {symbol} at {new_price} for a profit")
                        break

                    # Check for loss cutoff
                    elif new_price <= current_price * (1 - loss_cutoff):
                        send_order(
                            symbol=symbol,
                            qty=order_size_in_dollars,
                            side='sell',
                            type='market',
                            time_in_force='gtc'
                        )
                        print(f"Sold ${order_size_in_dollars} of {symbol} at {new_price} to cut loss")
                        break

                    time.sleep(1)  # Wait 1 second before checking the price again

                time.sleep(60)  # Wait 60 seconds before starting the next trade cycle
        else:
            liquidate.liquidate()
            print("Market Closed")
            time.sleep(60)    
    except Exception as e:
        print(f"An error occurred with {symbol}: {e}")

# Run the strategy for each stock symbol in a separate thread
while True:
    if marketOpen():
        threads = []
        for symbol in symbols:
            thread = threading.Thread(target=scalp_trade, args=(symbol,))
            thread.start()
            threads.append(thread)

        # Ensure all threads complete
        for thread in threads:
            thread.join()
    else:
        print("Market Closed")
        liquidate.liquidate()
        time.sleep(60)

