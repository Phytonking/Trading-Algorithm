import requests
from dotenv import dotenv_values

config = dotenv_values(".env")

def send_order(symbol, qty, side, type, time_in_force):
    url = "https://paper-api.alpaca.markets/v2/orders"

    payload = {
        "side": side,
        "type": type,
        "time_in_force": "day",
        "symbol": symbol,
        "notional": qty
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "APCA-API-KEY-ID": config["alpaca-key"],
        "APCA-API-SECRET-KEY": config["secret-key"]
    }

    response = requests.post(url, json=payload, headers=headers)
    print(response.text)
    return response.json()