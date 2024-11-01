import requests

from dotenv import dotenv_values

def active_stocks():
    url = "https://data.alpaca.markets/v1beta1/screener/stocks/most-actives?by=volume&top=20"
    config = dotenv_values(".env")
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": config["alpaca-key"],
        "APCA-API-SECRET-KEY": config["secret-key"]
    }

    response = requests.get(url, headers=headers)

    print(response.text)

active_stocks()