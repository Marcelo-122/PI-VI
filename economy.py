import requests
import pandas as pd
import json
from datetime import datetime

class IMFDataCollector:
    """
    Classe para coletar dados econômicos do IMF DataMapper API
    Documentação da API: https://datahelp.imf.org/knowledgebase/articles/667681-using-json-restful-web-service
    """
    
    def __init__(self):
        self.base_url = "https://www.imf.org/external/datamapper/api/v1"
        self.database_id = "IFS"  # International Financial Statistics
        
    def get_country_list(self):
        """Obtém a lista de países disponíveis do IMF DataMapper"""
        # Usando um indicador comum para obter a lista de países
        url = f"{self.base_url}/PCPIPCH"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                countries = {}
                # Extrai os códigos dos países da estrutura de valores
                if 'values' in data and 'PCPIPCH' in data['values']:
                    for country_code in data['values']['PCPIPCH'].keys():
                        countries[country_code] = country_code
                return countries
            else:
                print(f"Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching country list: {e}")
            return None
    
    def get_inflation_data(self, country_codes, start_year=2010, end_year=2024):
        """
        Obtém dados de inflação para países especificados usando o IMF DataMapper API
        
        Parâmetros:
        - country_codes: lista de códigos ISO dos países (ex: ['USA', 'GBR', 'BRA'])
        - start_year: ano inicial para os dados
        - end_year: ano final para os dados
        
        Nota: IMF DataMapper usa códigos ISO de 3 letras (USA, GBR, BRA, JPN, etc.)
        """
        
        # PCPIPCH: Taxa de inflação, preços médios ao consumidor (variação percentual)
        indicator = "PCPIPCH"
        
        all_data = []
        
        for country in country_codes:
            url = f"{self.base_url}/{indicator}/{country}"
            
            print(f"Fetching data for {country}...")
            
            try:
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'values' in data and indicator in data['values']:
                        country_data = data['values'][indicator].get(country, {})
                        
                        for year, value in country_data.items():
                            try:
                                year_int = int(year)
                                if start_year <= year_int <= end_year and value is not None:
                                    all_data.append({
                                        'country': country,
                                        'year': year_int,
                                        'inflation_rate': float(value)
                                    })
                            except (ValueError, TypeError):
                                continue
                else:
                    print(f"Error for {country}: {response.status_code}")
                    
            except Exception as e:
                print(f"Error fetching data for {country}: {e}")
        
        if all_data:
            df = pd.DataFrame(all_data)
            df = df.sort_values(['country', 'year']).reset_index(drop=True)
            return df
        else:
            return None
    
    def _parse_inflation_data(self, data):
        """Analisa a resposta JSON em um DataFrame pandas"""
        records = []
        
        try:
            series = data['CompactData']['DataSet']['Series']
            
            # Trata série única (retorna dict) vs múltiplas séries (retorna lista)
            if isinstance(series, dict):
                series = [series]
            
            for s in series:
                country = s['@REF_AREA']
                
                # Handle observations
                obs = s.get('Obs', [])
                if isinstance(obs, dict):
                    obs = [obs]
                
                for o in obs:
                    records.append({
                        'country': country,
                        'period': o['@TIME_PERIOD'],
                        'inflation_rate': float(o['@OBS_VALUE'])
                    })
            
            df = pd.DataFrame(records)
            return df
        
        except Exception as e:
            print(f"Error parsing data: {e}")
            return None
    
    def get_annual_inflation(self, country_codes, start_year=2010, end_year=2024):
        """
        Get annual average inflation data
        This is the same as get_inflation_data for the DataMapper API
        """
        return self.get_inflation_data(country_codes, start_year, end_year)


# Example usage
if __name__ == "__main__":
    collector = IMFDataCollector()
    
    # Códigos dos países: USA (Estados Unidos), BRA (Brasil), GBR (Reino Unido), JPN (Japão)
    # Nota: IMF DataMapper usa códigos ISO de 3 letras
    countries_to_fetch = ['USA', 'BRA', 'GBR', 'JPN']
    
    print(f"\nObtendo dados para: {', '.join(countries_to_fetch)}")
    print(f"Período: 2020-2024\n")
    
    # Obter dados mensais de inflação
    df = collector.get_inflation_data(
        country_codes=countries_to_fetch,
        start_year=2020,
        end_year=2024
    )
    
    if df is not None and not df.empty:
        print("\nData collected successfully!")
        print(f"Total records: {len(df)}")
        print("\nFirst 10 rows:")
        print(df.head(10))
        
        print("\nSummary statistics by country:")
        print(df.groupby('country')['inflation_rate'].describe())
        
        # Salvar em JSON (vários formatos disponíveis)
        
        # Formato 1: Formato de registros (lista de objetos) - mais comum para APIs
        output_file_json = "imf_inflation_data.json"
        df.to_json(output_file_json, orient='records', indent=2)
        print(f"\nDados salvos em: {output_file_json} (formato de registros JSON)")
        
        # Formato 2: Agrupado por país (estrutura aninhada)
        output_file_nested = "imf_inflation_data_nested.json"
        nested_data = {}
        for country in df['country'].unique():
            country_df = df[df['country'] == country]
            nested_data[country] = country_df[['year', 'inflation_rate']].to_dict('records')
        
        with open(output_file_nested, 'w') as f:
            json.dump(nested_data, f, indent=2)
        print(f"Dados salvos em: {output_file_nested} (formato aninhado por país)")
        
        # Formato 3: Formato pronto para API com metadados
        output_file_api = "imf_inflation_data_api.json"
        api_response = {
            "metadata": {
                "source": "IMF DataMapper API",
                "indicator": "PCPIPCH",
                "indicator_name": "Inflation rate, average consumer prices (Annual percent change)",
                "countries": countries_to_fetch,
                "start_year": 2020,
                "end_year": 2024,
                "total_records": len(df),
                "generated_at": datetime.now().isoformat()
            },
            "data": df.to_dict('records')
        }
        
        with open(output_file_api, 'w') as f:
            json.dump(api_response, f, indent=2)
        print(f"Dados salvos em: {output_file_api} (formato API com metadados)")
        
    else:
        print("Nenhum dado recuperado")
    
    # Exemplo 3: Obter dados anuais de inflação
    print("\n" + "=" * 60)
    print("EXEMPLO: Taxas de Inflação Anuais")
    print("=" * 60)
    
    df_annual = collector.get_annual_inflation(
        country_codes=countries_to_fetch,
        start_year=2015,
        end_year=2024
    )
    
    if df_annual is not None and not df_annual.empty:
        print("\nDados anuais de inflação:")
        print(df_annual)