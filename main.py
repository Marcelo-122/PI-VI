import requests
from config import cfg
from tabulate import tabulate
from datetime import datetime

url = "https://api.isthereanydeal.com/games/history/v2"
params = {
    "key": cfg.API_KEY,
    "id": "018d937f-21e1-728e-86d7-9acb3c59f2bb"
}

def fetch_price_history():
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json() 
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def format_price_history(data):
    if not data or not isinstance(data, list):
        return [["No data available"]]

    rows = []
    for item in data:
        timestamp = datetime.fromisoformat(item["timestamp"]).strftime("%Y-%m-%d %H:%M")
        shop_name = item["shop"]["name"]
        price = item["deal"]["price"]["amount"]
        currency = item["deal"]["price"]["currency"]
        cut = item["deal"]["cut"]
        rows.append([timestamp, shop_name, f"{price:.2f} {currency}", f"{cut}%"])

    return rows

def main():
    data = fetch_price_history()
    table = format_price_history(data)
    print(tabulate(table, headers=["Date", "Shop", "Price", "Discount"], tablefmt="fancy_grid"))

if __name__ == "__main__":
    main()
