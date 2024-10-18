from dotenv import dotenv_values

config = dotenv_values(".env")

def marketOpen():
    import requests

    url = "https://paper-api.alpaca.markets/v2/clock"

    headers = {"accept": "application/json", "APCA-API-KEY-ID": config["alpaca-key"], "APCA-API-SECRET-KEY": config["secret-key"]}

    response = requests.get(url, headers=headers)

    print(response.text)
    return response.json()["is_open"]