import pandas as pd
from datetime import datetime
import imfp


class IMFEconomicDataCollector:
    """Coleta indicadores econômicos do IMF e exporta para CSV"""

    def __init__(self):
        self.indicators_info = {
            "PCPIPCH": "taxa de inflação, média de preços consumidores (percentual anual)",
            "NGDPDPC": "PIB per capita, preços atuais (dólares americanos)",
            "PPPPC": "PIB per capita, PPP (dólares internacionais atuais)",
        }

    def collect_data(self, countries, indicators, start_year, end_year):
        """
        Coleta dados usando o pacote imfp

        Parâmetros:
        - countries: lista de códigos de 3 letras do país (por exemplo, ['USA', 'BRA'])
        - indicators: lista de códigos de indicadores (por exemplo, ['PCPIPCH', 'NGDPDPC'])
        - start_year: ano inicial (por exemplo, 2015)
        - end_year: ano final (por exemplo, 2024)
        """

        all_data = []

        for indicator in indicators:
            print(f"Coletando {indicator}...")

            try:
                # Fetch data from IMF World Economic Outlook (WEO) database
                df = imfp.imf_dataset(
                    database_id="WEO",
                    indicator=indicator,
                    country=countries,
                    start_year=start_year,
                    end_year=end_year,
                )

                if df is not None and not df.empty:
                    # Standardize column names
                    rename_map = {}

                    # Find year column
                    for col in ["TIME_PERIOD", "@TIME_PERIOD", "time_period"]:
                        if col in df.columns:
                            rename_map[col] = "year"
                            break

                    # Find country column
                    for col in ["REF_AREA", "@REF_AREA", "ref_area"]:
                        if col in df.columns:
                            rename_map[col] = "country"
                            break

                    # Find value column
                    for col in ["OBS_VALUE", "@OBS_VALUE", "obs_value"]:
                        if col in df.columns:
                            rename_map[col] = "value"
                            break

                    df = df.rename(columns=rename_map)

                    # Add indicator column and description
                    if "indicator" not in df.columns:
                        df["indicator"] = indicator
                    
                    df["indicator_description"] = self.indicators_info.get(
                        indicator, indicator
                    )

                    # Keep only relevant columns
                    cols_to_keep = [
                        "country", "year", "indicator", 
                        "indicator_description", "value"
                    ]
                    df = df[[col for col in cols_to_keep if col in df.columns]]

                    all_data.append(df)
                    print(f"  ✓ Collected {len(df)} records")
                else:
                    print("  ✗ No data found")

            except Exception as e:
                print(f"  ✗ Error: {e}")

        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()

    def prepare_csv_formats(self, df):
        """Prepara dados em diferentes formatos CSV"""
        
        if df.empty:
            print("✗ Nenhum dado disponível para exportar")
            return None

        # Clean data
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["year", "value"])

        formats = {}

        # Formato 1: Long format (original)
        formats["long_format"] = df.copy()

        # Formato 2: Wide format - indicadores como colunas
        wide_df = df.pivot_table(
            index=["country", "year"],
            columns="indicator",
            values="value",
            aggfunc="first",
        ).reset_index()
        
        # Renomear colunas com descrições
        col_rename = {
            ind: f"{ind}_{self.indicators_info.get(ind, ind)[:30]}"
            for ind in df["indicator"].unique()
        }
        wide_df = wide_df.rename(columns=col_rename)
        formats["wide_format"] = wide_df

        # Formato 3: Por país (um arquivo por país seria muito, mas podemos ter tudo marcado)
        formats["by_country"] = df.sort_values(["country", "year", "indicator"])

        return formats

    def export_to_csv(self, formats, base_filename="economic_indicators"):
        """Exporta dados para arquivos CSV"""
        
        files_created = []
        
        for format_name, df in formats.items():
            filename = f"{base_filename}_{format_name}.csv"
            df.to_csv(filename, index=False, encoding="utf-8")
            files_created.append(filename)
            print(f"✓ Arquivo criado: {filename} ({len(df)} linhas)")
        
        # Criar arquivo de metadados
        metadata_file = f"{base_filename}_metadata.csv"
        metadata = pd.DataFrame([
            {
                "field": "source",
                "value": "IMF (International Monetary Fund)"
            },
            {
                "field": "database",
                "value": "World Economic Outlook"
            },
            {
                "field": "generated_at",
                "value": datetime.now().isoformat()
            },
            {
                "field": "total_countries",
                "value": len(formats["long_format"]["country"].unique())
            },
            {
                "field": "total_indicators",
                "value": len(formats["long_format"]["indicator"].unique())
            },
            {
                "field": "year_range",
                "value": f"{formats['long_format']['year'].min()}-{formats['long_format']['year'].max()}"
            }
        ])
        metadata.to_csv(metadata_file, index=False, encoding="utf-8")
        files_created.append(metadata_file)
        print(f"✓ Arquivo criado: {metadata_file}")
        
        return files_created




def main():
    """Main execution"""

    print("=" * 70)
    print("Coletor de dados econômicos do IMF - Export CSV")
    print("=" * 70)

    collector = IMFEconomicDataCollector()

    # Configuration
    countries = ["USA", "BRA", "ARG", "TUR", "JPN", "DEU"]
    indicators = ["PCPIPCH", "NGDPDPC", "PPPPC"]
    start_year = 2023
    end_year = 2024

    print(f"\nPaíses: {', '.join(countries)}")
    print(f"Período: {start_year}-{end_year}")
    print("\nIndicadores:")
    for ind in indicators:
        print(f"  • {ind}: {collector.indicators_info.get(ind, ind)}")

    print("\n" + "=" * 70)
    print("Coletando dados do IMF...")
    print("=" * 70 + "\n")

    # Collect data
    df = collector.collect_data(countries, indicators, start_year, end_year)

    if not df.empty:
        print("\n" + "=" * 70)
        print("Resumo dos dados coletados")
        print("=" * 70)
        print(f"Total de registros: {len(df)}")
        print("\nPor indicador:")
        print(df.groupby("indicator").size().to_string())
        print("\nPor país:")
        print(df.groupby("country").size().to_string())

        # Prepare CSV formats
        print("\n" + "=" * 70)
        print("Preparando arquivos CSV...")
        print("=" * 70 + "\n")
        
        formats = collector.prepare_csv_formats(df)
        
        if formats:
            # Export to CSV
            files = collector.export_to_csv(formats)
            
            print("\n" + "=" * 70)
            print("✓ PROCESSO CONCLUÍDO!")
            print("=" * 70)
            print(f"\nArquivos CSV criados: {len(files)}")
            print("\nFormatos disponíveis:")
            print("  • long_format: dados no formato longo (país, ano, indicador, valor)")
            print("  • wide_format: indicadores como colunas (ideal para gráficos)")
            print("  • by_country: ordenado por país (ideal para análise individual)")
            print("  • metadata: informações sobre a coleta")

        else:
            print("\n" + "=" * 70)
            print("✗ FALHA - Nenhum dado coletado")
            print("=" * 70)


if __name__ == "__main__":
    main()