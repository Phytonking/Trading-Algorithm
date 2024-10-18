import alpaca_trade_api as tradeapi
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dotenv import dotenv_values
from account import get_cash
from market_open import marketOpen
from submit_order import send_order
from bars import get_bars
from liquidate import liquidate

# Load API credentials
config = dotenv_values(".env")
API_KEY = config["alpaca-key"]
API_SECRET = config["secret-key"]
BASE_URL = 'https://paper-api.alpaca.markets'

# Initialize Alpaca API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

# Define stock symbols and parameters
symbols = [
    "XELA", "NAKD", "GNUS", "VERB", "MOGO", "IDEX", "CETX", "INUV", "CIDM", "PHUN",
    "ONCS", "TNXP", "ACST", "OSMT", "ADXS", "OGEN", "PULM", "DFFN", "BIOC", "ZOM",
    "TRCH", "CEI", "ZNOG", "FCEL", "RIG", "USEG", "VVPR", "GTE", "ALTO", "DNN",
    "NUZE", "RM", "FNVT", "ASAP", "MICT", "LMFA", "GRNQ", "BITF", "SOS", "RIOT"
]

profit_target = 0.001  # 0.1% profit
exact_loss_cutoff = 0.0005  # 0.05% loss (exact trigger)

def calculate_order_qty(symbol, budget):
    """Calculate how many shares can be bought within the budget."""
    latest_price = float(get_bars(symbol, "1Min", limit=1)["quote"]["bp"])
    qty = int(budget / latest_price)
    return max(qty, 1)  # Ensure at least one share

def scalp_trade(symbol):
    """Execute a scalp trade for a single stock symbol."""
    try:
        budget = float(get_cash()) / len(symbols)
        qty = calculate_order_qty(symbol, budget)

        if qty == 0:
            print(f"Insufficient funds to trade {symbol}.")
            return

        current_price = float(get_bars(symbol, "1Min", limit=1)["quote"]["bp"])
        send_order(symbol, qty, 'buy', 'market', 'gtc')
        print(f"Bought {qty} shares of {symbol} at {current_price}")

        while True:
            new_price = float(get_bars(symbol, "1Min", limit=1)["quote"]["bp"])

            # Check for profit target
            if new_price >= current_price * (1 + profit_target):
                send_order(symbol, qty, 'sell', 'market', 'gtc')
                print(f"Sold {qty} shares of {symbol} at {new_price} for a profit")
                break

            # Check for exact 0.05% loss
            elif new_price == current_price * (1 - exact_loss_cutoff):
                send_order(symbol, qty, 'sell', 'market', 'gtc')
                print(f"Sold {qty} shares of {symbol} at {new_price} to cut exact 0.05% loss")
                break

            time.sleep(2)  # Wait 2 seconds before checking the price again

    except Exception as e:
        print(f"Error trading {symbol}: {e}")

def main():
    """Run the trading strategy."""
    while True:
        if marketOpen():
            with ThreadPoolExecutor(max_workers=10) as executor:
                executor.map(scalp_trade, symbols)
        else:
            print("Market Closed. Liquidating positions...")
            liquidate()
            time.sleep(60)

if __name__ == "__main__":
    main()
