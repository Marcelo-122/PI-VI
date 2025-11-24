import json
import requests
from config import cfg


class GameLookup:
    def __init__(self):
        self.api_key = cfg.STEAM_API_KEY
        self.base_url = "https://api.isthereanydeal.com"

    def search_game(self, game_name, limit=5):
        """
        Busca um jogo pelo nome
        
        Args:
            game_name (str): Nome do jogo para buscar
            limit (int): Número máximo de resultados
            
        Returns:
            list: Lista de jogos encontrados
        """
        url = f"{self.base_url}/games/search/v1"
        params = {
            "key": self.api_key,
            "title": game_name,
            "results": limit
        }
        
        print(f"🔍 Buscando '{game_name}'...")
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            print(f"❌ Erro na busca: {response.status_code}")
            return []
        
        results = response.json()
        
        if not results:
            print("❌ Nenhum jogo encontrado")
            return []
        
        print(f"✅ Encontrados {len(results)} jogo(s)")
        return results

    def interactive_search(self, game_name):
        """
        Busca interativa - mostra opções e permite escolher
        
        Args:
            game_name (str): Nome do jogo
            
        Returns:
            dict: Jogo selecionado ou None
        """
        results = self.search_game(game_name)
        
        if not results:
            return None
        
        # Se houver apenas um resultado
        if len(results) == 1:
            return results[0]
        
        # Múltiplos resultados
        print(f"\n📋 Escolha um jogo:")
        print("-" * 60)
        for i, game in enumerate(results, 1):
            game_type = game.get('type', 'game').upper()
            print(f"{i}. {game['title']} ({game_type})")
        print("0. Cancelar")
        print("-" * 60)
        
        while True:
            try:
                choice = input(f"\nEscolha (0-{len(results)}): ")
                choice = int(choice)
                
                if choice == 0:
                    print("❌ Cancelado")
                    return None
                
                if 1 <= choice <= len(results):
                    selected = results[choice - 1]
                    print(f"✅ Selecionado: {selected['title']}")
                    return selected
                else:
                    print(f"⚠️  Escolha entre 0 e {len(results)}")
            except ValueError:
                print("⚠️  Digite um número válido")
            except KeyboardInterrupt:
                print("\n❌ Cancelado")
                return None

    def save_to_json(self, data, filename="game_lookup.json"):
        """
        Salva resultado da busca em JSON
        
        Args:
            data: Dados para salvar (dict ou list)
            filename (str): Nome do arquivo
        """
        if not data:
            print("⚠️  Nenhum dado para salvar")
            return
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Dados salvos em {filename}")

def main():
    lookup = GameLookup()
        
    # Busca interativa
    print("=" * 60)
    print("Busca interativa")
    print("=" * 60)
    selected = lookup.interactive_search("Elden Ring")
    if selected:
        lookup.save_to_json(selected, "selected_game.json")
    
if __name__ == "__main__":
    main()