import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, RootModel

from config import cfg

app = FastAPI(
    title="Historico de Preços de Jogos API",
    description="API para acesso ao histórico de preços de jogos",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PRICE_DATA_FILE = Path(__file__).parent / "price_history.json"
ECONOMIC_DATA_FILE = Path(__file__).parent / "economic_indicators.json"

try:
    with open(PRICE_DATA_FILE, "r") as f:
        price_data = json.load(f)
except FileNotFoundError:
    price_data = {"error": "Arquivo de dados de preços não encontrado"}

try:
    with open(ECONOMIC_DATA_FILE, "r") as f:
        economic_data = json.load(f)
except FileNotFoundError:
    economic_data = {"error": "Arquivo de dados econômicos não encontrado"}


class Price(BaseModel):
    timestamp: str
    shop: Dict[str, Any]
    deal: Dict[str, Any]


class PriceHistoryResponse(BaseModel):
    game_id: str
    last_updated: str
    start_date: str
    end_date: str
    prices: List[Price]


class Indicator(BaseModel):
    NGDPDPC: float
    PCPIPCH: float
    PPPPC: float


class EconomicDataPoint(BaseModel):
    period: int
    period_type: str
    indicators: Indicator


class CountryEconomicData(RootModel[List[EconomicDataPoint]]):
    pass


class EconomicIndicatorsResponse(BaseModel):
    metadata: Dict[str, Any]
    data: Dict[str, List[EconomicDataPoint]]


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Bem-vindo ao Historico de Preços de Jogos API",
        "endpoints": [
            "/prices - Retorna o histórico de preços de todos os jogos",
            "/prices/{game_id}?start_date=...&end_date=... - Retorna o histórico de preços de um jogo com filtro de data",
            "/prices/shop/{shop_id} - Retorna o preço mais recente de um jogo específico",
            "/economic-indicators - Retorna todos os indicadores econômicos",
            "/economic-indicators/{country} - Retorna os indicadores econômicos de um país específico",
            "/economic-indicators/{country}/{year} - Retorna os indicadores econômicos de um país específico em um ano específico",
        ],
    }


@app.get("/prices", response_model=PriceHistoryResponse, tags=["Prices"])
async def get_all_prices():
    if "error" in price_data:
        raise HTTPException(status_code=404, detail=price_data["error"])
    return price_data


@app.get("/prices/{game_id}", response_model=PriceHistoryResponse, tags=["Prices"])
async def get_prices_by_game_id(
    game_id: str,
    start_date: str = None,  # ISO 8601 format
    end_date: str = None,  # ISO 8601 format
):
    url = "https://api.isthereanydeal.com/games/history/v2"
    params = {"key": cfg.STEAM_API_KEY, "id": game_id}
    if start_date:
        params["since"] = start_date

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises an exception for bad status codes
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=503, detail=f"Error fetching data from API: {e}"
        )

    data = response.json()

    # Filter by end_date if provided
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            data = [
                entry
                for entry in data
                if datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                <= end_dt
            ]
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=400, detail="Invalid end_date format. Use ISO 8601."
            )

    if not isinstance(data, list) or not data:
        raise HTTPException(
            status_code=404, detail=f"No price history found for game ID {game_id}."
        )

    start_date = data[-1]["timestamp"]
    end_date = data[0]["timestamp"]

    processed_data = {
        "game_id": game_id,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "start_date": start_date,
        "end_date": end_date,
        "prices": data,
    }

    return processed_data


@app.get("/prices/shop/{shop_id}", tags=["Prices"])
async def get_prices_by_shop(shop_id: int):
    if "error" in price_data:
        raise HTTPException(status_code=404, detail=price_data["error"])

    shop_prices = [
        price
        for price in price_data.get("prices", [])
        if price.get("shop", {}).get("id") == shop_id
    ]

    if not shop_prices:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum preço encontrado para a loja com ID {shop_id}",
        )

    return shop_prices


@app.get(
    "/economic-indicators",
    response_model=EconomicIndicatorsResponse,
    tags=["Economic Indicators"],
)
async def get_economic_indicators():
    if "error" in economic_data:
        raise HTTPException(status_code=404, detail=economic_data["error"])
    return economic_data


@app.get(
    "/economic-indicators/{country}",
    response_model=List[EconomicDataPoint],
    tags=["Economic Indicators"],
)
async def get_economic_indicators_by_country(country: str):
    if "error" in economic_data:
        raise HTTPException(status_code=404, detail=economic_data["error"])

    country_data = economic_data.get("data", {}).get(country.upper())

    if not country_data:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum dado encontrado para o país com código {country}",
        )

    return country_data


@app.get(
    "/economic-indicators/{country}/{year}",
    response_model=EconomicDataPoint,
    tags=["Economic Indicators"],
)
async def get_economic_indicators_by_country_and_year(country: str, year: int):
    if "error" in economic_data:
        raise HTTPException(status_code=404, detail=economic_data["error"])

    country_data = economic_data.get("data", {}).get(country.upper())

    if not country_data:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum dado encontrado para o país com código {country}",
        )

    for data_point in country_data:
        if data_point.get("period") == year:
            return data_point

    raise HTTPException(
        status_code=404,
        detail=f"Nenhum dado encontrado para o ano {year} no país {country}",
    )


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
