import json
from datetime import datetime

import requests

from config import cfg


class GamePriceAnalyzer:
    def __init__(self):
        self.api_key = cfg.STEAM_API_KEY
        self.game_id = "018d937f-21e1-728e-86d7-9acb3c59f2bb"
        self.base_url = "https://api.isthereanydeal.com"

    def get_price_history(self, start_date=None, end_date=None):
        """Busca o histórico de preços com filtros de intervalo de datas

        Args:
            start_date (str, optional): Data de início no formato ISO (ex: 2023-01-01)
            end_date (str, optional): Data de término no formato ISO (ex: 2023-12-31)

        Returns:
            list: Lista de entradas de preço filtradas
        """
        url = f"{self.base_url}/games/history/v2"
        params = {"key": self.api_key, "id": self.game_id}

        if start_date:
            params["since"] = start_date

        print(f"Buscando dados da API...")
        response = requests.get(url, params=params)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if not isinstance(data, list):
                print("Formato de resposta inesperado")
                return []

            # Aplica filtros de data
            filtered_data = []
            for entry in data:
                try:
                    timestamp = entry.get("timestamp", "")
                    if not timestamp:
                        continue

                    entry_date = datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00")
                    )

                    # Aplica filtro de data de início
                    if start_date:
                        start = datetime.fromisoformat(
                            start_date.replace("Z", "+00:00")
                        )
                        if entry_date < start:
                            continue

                    # Aplica filtro de data de término
                    if end_date:
                        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                        if entry_date > end:
                            continue

                    filtered_data.append(entry)
                except (ValueError, AttributeError) as e:
                    print(f"Erro ao processar entrada: {e}")
                    continue

            print(f"Encontrados {len(filtered_data)} registros após filtrar")
            return filtered_data

        print(f"Erro na API: {response.text}")
        return []

    def save_price_history_to_json(self, data, filename="price_history.json"):
        """Salva o histórico de preços do jogo em um arquivo JSON"""
        if not data:
            print(f"Nenhum dado para salvar em {filename}")
            return

        # Process the data to a cleaner format
        processed_data = {
            "game_id": self.game_id,
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "prices": [],
        }

        for entry in data:
            price_entry = {
                "timestamp": entry.get("timestamp", ""),
                "shop": {
                    "id": entry.get("shop", {}).get("id", ""),
                    "name": entry.get("shop", {}).get("name", ""),
                },
                "deal": {
                    "price": entry.get("deal", {}).get("price", {}),
                    "regular": entry.get("deal", {}).get("regular", {}),
                    "cut": entry.get("deal", {}).get("cut", 0),
                },
            }
            processed_data["prices"].append(price_entry)

        # Save to JSON file with pretty printing
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)

        print(f"Histórico de preços salvo em {filename}")
        return processed_data

    def run_analysis(self, start_date=None, end_date=None):
        """Realiza análise do histórico de preços com filtros de intervalo de datas

        Args:
            start_date (str, optional): Data de início no formato ISO (ex: 2023-01-01)
            end_date (str, optional): Data de término no formato ISO (ex: 2023-12-31)
        """
        print("Iniciando análise do histórico de preços...")

        start_date = start_date or "2012-01-01T00:00:00Z"
        end_date = end_date or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Mostra os filtros ativos
        print(f"\n=== Filtros Ativos ===")
        print(f"- Data inicial: {start_date}")
        print(f"- Data final: {end_date}")

        print("\nBuscando histórico de preços...")
        history_data = self.get_price_history(start_date=start_date, end_date=end_date)

        if not history_data:
            print("\nNenhum dado encontrado com os filtros fornecidos.")
            return

        result = self.save_price_history_to_json(history_data)
        if result and "prices" in result and result["prices"]:
            prices = result["prices"]
            latest = prices[0]
            oldest = prices[-1]

            print("\n=== Resumo do Histórico ===")
            print(f"Total de registros: {len(prices)}")

            print("\nÚltimo preço:")
            self._print_price_entry(latest)

            if len(prices) > 1:
                print("\nVariação de preço:")
                self._print_price_entry(oldest, "Preço mais antigo")

                # Calcula variação percentual
                old_price = oldest["deal"]["price"].get("amount")
                new_price = latest["deal"]["price"].get("amount")
                if old_price and new_price and old_price > 0:
                    change = ((new_price - old_price) / old_price) * 100
                    change_type = "aumento" if change > 0 else "queda"
                    print(f"Variação: {abs(change):.1f}% de {change_type}")

        print("\nAnálise concluída! Verifique o arquivo price_history.json")

    def _print_price_entry(self, entry, label="Preço"):
        """Helper para exibir informações de uma entrada de preço"""
        print(f"{label}:")
        print(f"- Data: {entry['timestamp']}")
        print(f"- Loja: {entry['shop']['name']}")
        price = entry["deal"]["price"]
        print(f"- Valor: {price.get('amount')} {price.get('currency', '')}")
        if entry["deal"].get("cut"):
            print(f"- Desconto: {entry['deal']['cut']}%")


if __name__ == "__main__":
    analyzer = GamePriceAnalyzer()

    # Exemplo de uso com intervalo de datas
    analyzer.run_analysis(
        start_date="2023-01-01T00:00:00Z",  # Data de início
        end_date="2023-06-30T23:59:59Z",  # Data de término
    )
