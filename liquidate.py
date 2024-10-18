from dotenv import dotenv_values

config = dotenv_values(".env")

def liquidate():
    import requests

    url = "https://paper-api.alpaca.markets/v2/positions?cancel_orders=true"

    headers = {"accept": "application/json", "APCA-API-KEY-ID": config["alpaca-key"], "APCA-API-SECRET-KEY": config["secret-key"]}

    response = requests.delete(url, headers=headers)

    print(response.text)