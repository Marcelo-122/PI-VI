import requests
from config import cfg
from tabulate import tabulate

url = "https://api.isthereanydeal.com/games/history/v2"
params = {
    "key": cfg.API_KEY,
    "id": "018d937f-21e1-728e-86d7-9acb3c59f2bb" 
}

r = requests.get(url, params=params)
print(tabulate(r.json(), headers="keys", tablefmt="fancy_grid"))