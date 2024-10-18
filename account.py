from dotenv import dotenv_values

config = dotenv_values(".env")
def get_info():
    import requests

    url = "https://paper-api.alpaca.markets/v2/account"

    headers = {"accept": "application/json", "APCA-API-KEY-ID": config["alpaca-key"], "APCA-API-SECRET-KEY": config["secret-key"]}

    response = requests.get(url, headers=headers)
    print(response.text)
    return response.json()

def get_cash():
    return get_info()["buying_power"]