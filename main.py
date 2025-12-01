import csv
from datetime import datetime

import requests

from config import cfg


class GamePriceAnalyzer:
    def __init__(self):
        self.api_key = cfg.STEAM_API_KEY
        self.game_id = "018d937f-21e1-728e-86d7-9acb3c59f2bb"
        self.base_url = "https://api.isthereanydeal.com"

    def get_price_history(self, start_date=None, end_date=None, shops=None, country=None):
        """Busca o histórico de preços com filtros de intervalo de datas e lojas

        Args:
            start_date (str, optional): Data de início no formato ISO (ex: 2023-01-01)
            end_date (str, optional): Data de término no formato ISO (ex: 2023-12-31)
            shops (list, optional): Lista de IDs de lojas para filtrar (ex: ['steam'])
            country (str, optional): Código do país (ex: 'US', 'BR', 'AR', 'TR', 'JP', 'DE')

        Returns:
            list: Lista de entradas de preço filtradas
        """
        url = f"{self.base_url}/games/history/v2"
        params = {"key": self.api_key, "id": self.game_id}

        if start_date:
            params["since"] = start_date

        # Adiciona filtro de lojas se fornecido
        if shops:
            params["shops"] = ",".join(map(str, shops))
        
        # Adiciona filtro de país se fornecido
        if country:
            params["country"] = country

        print("Buscando dados da API...")
        response = requests.get(url, params=params)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if not isinstance(data, list):
                print("Formato de resposta inesperado")
                return []

            print(f"Total de registros recebidos da API: {len(data)}")
            
            # Debug: mostra as primeiras lojas encontradas
            if data and len(data) > 0:
                unique_shops = set()
                for entry in data[:10]:  # Verifica os primeiros 10
                    shop_id = entry.get("shop", {}).get("id", "")
                    shop_name = entry.get("shop", {}).get("name", "")
                    unique_shops.add(f"{shop_id} ({shop_name})")
                print(f"Exemplos de lojas encontradas: {', '.join(list(unique_shops)[:5])}")

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

    def save_price_history_to_csv(self, data, filename="price_history.csv", country=None):
        """Salva o histórico de preços do jogo em um arquivo CSV"""
        if not data:
            print(f"Nenhum dado para salvar em {filename}")
            return

        # Adiciona o país ao nome do arquivo se fornecido
        if country:
            filename = f"price_history_{country}.csv"

        processed_data = []
        for entry in data:
            price_info = entry.get("deal", {}).get("price", {})
            regular_info = entry.get("deal", {}).get("regular", {})

            processed_data.append(
                {
                    "timestamp": entry.get("timestamp", ""),
                    "shop_id": entry.get("shop", {}).get("id", ""),
                    "shop_name": entry.get("shop", {}).get("name", ""),
                    "price_amount": price_info.get("amount"),
                    "price_currency": price_info.get("currency"),
                    "regular_amount": regular_info.get("amount"),
                    "regular_currency": regular_info.get("currency"),
                    "cut": entry.get("deal", {}).get("cut", 0),
                }
            )

        if not processed_data:
            print("Nenhum dado processado para salvar.")
            return

        # Salva o histórico de preços em um arquivo CSV
        with open(filename, "w", newline="", encoding="utf-8") as f:
            fieldnames = processed_data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(processed_data)

        print(f"Histórico de preços salvo em {filename}")
        return processed_data

    def run_analysis(self, start_date=None, end_date=None, shops=None, country=None):
        """Realiza análise do histórico de preços com filtros de intervalo de datas e lojas

        Args:
            start_date (str, optional): Data de início no formato ISO (ex: 2023-01-01)
            end_date (str, optional): Data de término no formato ISO (ex: 2023-12-31)
            shops (list, optional): Lista de IDs de lojas para filtrar (ex: ['steam'])
            country (str, optional): Código do país (ex: 'US', 'BR', 'AR', 'TR', 'JP', 'DE')
        """
        print("Iniciando análise do histórico de preços...")

        start_date = start_date or "2012-01-01T00:00:00Z"
        end_date = end_date or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Mostra os filtros ativos
        print("\n=== Filtros Ativos ===")
        print(f"- Data inicial: {start_date}")
        print(f"- Data final: {end_date}")
        if shops:
            print(f"- Lojas: {', '.join(map(str, shops))}")
        if country:
            print(f"- País: {country}")

        print("\nBuscando histórico de preços...")
        history_data = self.get_price_history(
            start_date=start_date, end_date=end_date, shops=shops, country=country
        )

        if not history_data:
            print("\nNenhum dado encontrado com os filtros fornecidos.")
            return

        prices = self.save_price_history_to_csv(history_data, country=country)
        if prices:
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
                old_price = oldest["price_amount"]
                new_price = latest["price_amount"]
                if old_price and new_price and old_price > 0:
                    change = ((new_price - old_price) / old_price) * 100
                    change_type = "aumento" if change > 0 else "queda"
                    print(f"Variação: {abs(change):.1f}% de {change_type}")

        print("\nAnálise concluída! Verifique o arquivo price_history.csv")

    def _print_price_entry(self, entry, label="Preço"):
        """Helper para exibir informações de uma entrada de preço"""
        print(f"{label}:")
        print(f"- Data: {entry['timestamp']}")
        print(f"- Loja: {entry['shop_name']}")
        print(f"- Valor: {entry['price_amount']} {entry['price_currency']}")
        if entry.get("cut"):
            print(f"- Desconto: {entry['cut']}%")


if __name__ == "__main__":
    analyzer = GamePriceAnalyzer()

    # Lista de países para buscar
    countries = ["US", "BR", "AR", "TR", "JP", "DE"]  # USA, BRA, ARG, TUR, JPN, DEU
    
    # Busca dados para cada país
    for country in countries:
        print(f"\n{'='*60}")
        print(f"Buscando dados para: {country}")
        print(f"{'='*60}")
        
        analyzer.run_analysis(
            start_date="2005-01-01T00:00:00Z",
            end_date="2025-11-30T23:59:59Z",
            shops=[61],  # Mantém o parâmetro mas não filtra manualmente
            country=country
        )