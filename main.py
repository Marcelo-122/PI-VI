import csv
import json
import requests
from config import cfg


class GamePriceAnalyzer:
    def __init__(self):
        self.api_key = cfg.API_KEY
        self.game_id = "018d937f-21e1-728e-86d7-9acb3c59f2bb"
        self.base_url = "https://api.isthereanydeal.com"

    def get_price_history(self, since_date=None):
        """Traz o histórico de preços do jogo"""
        url = f"{self.base_url}/games/history/v2"
        params = {"key": self.api_key, "id": self.game_id}

        if since_date:
            params["since"] = since_date

        print(f"URL da API: {url}")
        print(f"Parâmetros da API: {params}")

        response = requests.get(url, params=params)
        print(f"Código de Status da Resposta: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Tipo de dados da resposta: {type(data)}")
            if isinstance(data, dict):
                print(f"Chaves da resposta: {list(data.keys())}")
            elif isinstance(data, list):
                print(f"Comprimento da lista de resposta: {len(data)}")
            else:
                print(f"Conteúdo da resposta: {data}")
            return data
        else:
            print(f"Erro na API: {response.text}")
            return None

    def save_price_history_to_csv(self, data, filename="price_history.csv"):
        """Salva o histórico de preços do jogo em um arquivo CSV"""
        if not data:
            print(f"Nenhum dado para salvar para {filename}")
            return

        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            if isinstance(data, list):
                # trata a resposta como uma lista (formato atual da API)
                fieldnames = [
                    "timestamp",
                    "shop_id",
                    "shop_name",
                    "price_amount",
                    "price_currency",
                    "regular_amount",
                    "regular_currency",
                    "discount_cut",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for entry in data:
                    writer.writerow(
                        {
                            "timestamp": entry.get("timestamp", ""),
                            "shop_id": entry.get("shop", {}).get("id", ""),
                            "shop_name": entry.get("shop", {}).get("name", ""),
                            "price_amount": entry.get("deal", {})
                            .get("price", {})
                            .get("amount", ""),
                            "price_currency": entry.get("deal", {})
                            .get("price", {})
                            .get("currency", ""),
                            "regular_amount": entry.get("deal", {})
                            .get("regular", {})
                            .get("amount", ""),
                            "regular_currency": entry.get("deal", {})
                            .get("regular", {})
                            .get("currency", ""),
                            "discount_cut": entry.get("deal", {}).get("cut", ""),
                        }
                    )
            elif isinstance(data, dict):
                # trata a resposta como um dicionário
                rows = []
                for shop_id, shop_data in data.items():
                    if isinstance(shop_data, dict):
                        for date, price_info in shop_data.items():
                            if isinstance(price_info, dict):
                                rows.append(
                                    {
                                        "shop_id": shop_id,
                                        "date": date,
                                        "price": price_info.get("price", ""),
                                        "cut": price_info.get("cut", ""),
                                        "regular": price_info.get("regular", ""),
                                    }
                                )

                if rows:
                    fieldnames = ["shop_id", "date", "price", "cut", "regular"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
            else:
                # trata outros formatos de dados
                writer = csv.writer(csvfile)
                writer.writerow(["raw_data"])
                writer.writerow([json.dumps(data)])

        print(f"Histórico de preços salvo em {filename}")

    def run_analysis(self, custom_since_date=None):
        """Realiza análise do histórico de preços e gera arquivo CSV"""
        print("Iniciando análise do histórico de preços...")

        since_date = None
        if custom_since_date:
            since_date = custom_since_date
            print(f"Usando data personalizada: {since_date}")

        print("Buscando histórico de preços...")
        history_data = self.get_price_history(since_date)
        if history_data:
            self.save_price_history_to_csv(history_data)
            print("Histórico de preços salvo!")
            if isinstance(history_data, list) and len(history_data) > 0:
                display_data = []
                for entry in history_data:
                    display_data.append(
                        {
                            "Data": entry.get("timestamp", "")[:10],
                            "Loja": entry.get("shop", {}).get("name", ""),
                            "Preço": f"{entry.get('deal', {}).get('price', {}).get('amount', '')} {entry.get('deal', {}).get('price', {}).get('currency', '')}",
                            "Preço Normal": f"{entry.get('deal', {}).get('regular', {}).get('amount', '')} {entry.get('deal', {}).get('regular', {}).get('currency', '')}",
                            "Desconto": f"{entry.get('deal', {}).get('cut', '')}%",
                        }
                    )
        else:
            print("Nenhum histórico de preços encontrado")

        print("\nAnálise concluída! Arquivo CSV gerado:")
        print("- price_history.csv: Histórico de preços")


# Main execution
if __name__ == "__main__":
    analyzer = GamePriceAnalyzer()
    
    analyzer.run_analysis(custom_since_date="2012-01-01T00:00:00Z")

