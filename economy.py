import json
from datetime import datetime
import imfp
import pandas as pd


class IMFEconomicDataCollector:
    """Coleta indicadores econômicos do IMF"""

    def __init__(self):
        self.indicators_info = {
            "PCPIPCH": "taxa de inflação, média de preços consumidores (percentual anual)",
            "NGDPDPC": "PIB per capita, preços atuais (dólares americanos)",
            "PPPPC": "PIB per capita, PPP (dólares internacionais atuais)",
            "NGDP_RPCH": "PIB, preços constantes (percentual anual)",
            "LUR": "taxa de desemprego (percentual do total da força de trabalho)",
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
                    # Standardize column names - handle different possible names
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

                    # Add indicator column if not present
                    if "indicator" not in df.columns:
                        df["indicator"] = indicator

                    # Keep only relevant columns
                    cols_to_keep = ["country", "year", "indicator", "value"]
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

    def format_for_api(self, df):
        """Formata dados para consumo na API como JSON"""

        if df.empty:
            return {
                "error": "Nenhum dado disponível",
                "message": "Falha ao coletar dados do IMF",
            }

        # Validate required columns
        required_cols = ["country", "year", "indicator", "value"]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            return {
                "error": "Colunas obrigatórias ausentes",
                "missing": missing_cols,
                "available": df.columns.tolist(),
            }

        # Clean and convert data types
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["year", "value"])

        # Pivot data so each country-year has all indicators
        pivot_df = df.pivot_table(
            index=["country", "year"],
            columns="indicator",
            values="value",
            aggfunc="first",
        ).reset_index()

        # Build JSON structure
        result = {
            "metadata": {
                "source": "IMF (International Monetary Fund)",
                "database": "World Economic Outlook",
                "indicators": {
                    code: self.indicators_info.get(code, code)
                    for code in df["indicator"].unique()
                },
                "countries": sorted(df["country"].unique().tolist()),
                "year_range": {
                    "start": int(df["year"].min()),
                    "end": int(df["year"].max()),
                },
                "total_records": len(pivot_df),
                "generated_at": datetime.now().isoformat(),
            },
            "data": {},
        }

        # Group by country
        for country in pivot_df["country"].unique():
            country_data = pivot_df[pivot_df["country"] == country].copy()
            country_data = country_data.sort_values("year")

            result["data"][country] = []

            for _, row in country_data.iterrows():
                year_data = {
                    "period": int(row["year"]),
                    "period_type": "year",
                    "indicators": {},
                }

                # Add all economic indicators
                for col in country_data.columns:
                    if col not in ["country", "year"] and pd.notna(row[col]):
                        year_data["indicators"][col] = float(row[col])

                result["data"][country].append(year_data)

        return result

    def export_to_json(self, data, filename="economic_indicators.json"):
        """Export data to JSON file"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Data exported to: {filename}")


def main():
    """Main execution"""

    print("=" * 70)
    print("Coletor de dados econômicos do IMF")
    print("=" * 70)

    collector = IMFEconomicDataCollector()

    # Configuration
    countries = ["USA", "BRA", "GBR", "JPN", "DEU", "FRA", "CAN"]
    indicators = ["PCPIPCH", "NGDPDPC", "PPPPC"]
    start_year = 2018
    end_year = 2024

    print(f"\nCountries: {', '.join(countries)}")
    print(f"Period: {start_year}-{end_year}")
    print("\nIndicators:")
    for ind in indicators:
        print(f"  • {ind}: {collector.indicators_info.get(ind, ind)}")

    print("\n" + "=" * 70)
    print("Coletando dados...")
    print("=" * 70 + "\n")

    # Collect data
    df = collector.collect_data(countries, indicators, start_year, end_year)

    # Process and export
    if not df.empty:
        print("\n" + "=" * 70)
        print("Resumo")
        print("=" * 70)
        print(f"Total de registros: {len(df)}")
        print("\nPor indicador:")
        print(df.groupby("indicator").size().to_string())
        print("\nPor país:")
        print(df.groupby("country").size().to_string())

        # Format and export
        api_data = collector.format_for_api(df)
        collector.export_to_json(api_data, "economic_indicators.json")

        print("\n" + "=" * 70)
        print("✓ SUCCESS!")
        print("=" * 70)
        print("\nYou can now use 'economic_indicators.json' in your API")

    else:
        print("\n" + "=" * 70)
        print("✗ FAILED - No data collected")
        print("=" * 70)


if __name__ == "__main__":
    main()
