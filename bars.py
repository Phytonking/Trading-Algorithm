import requests
from dotenv import dotenv_values

config = dotenv_values(".env")

def get_bars(stock, timeframe, limit):
    import requests

    url = f"https://data.alpaca.markets/v2/stocks/{stock}/quotes/latest?feed=iex"

    headers = {"accept": "application/json", "APCA-API-KEY-ID": config["alpaca-key"],
        "APCA-API-SECRET-KEY": config["secret-key"]}

    response = requests.get(url, headers=headers)

    print(response.text)
    return response.json()