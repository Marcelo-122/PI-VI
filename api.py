from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import json
from pathlib import Path
import uvicorn

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

DATA_FILE = Path(__file__).parent / "price_history.json"

try:
    with open(DATA_FILE, "r") as f:
        price_data = json.load(f)
except FileNotFoundError:
    price_data = {"error": "Arquivo de dados de preços não encontrado"}


class Price(BaseModel):
    timestamp: str
    shop: Dict[str, Any]
    deal: Dict[str, Any]


class PriceHistoryResponse(BaseModel):
    game_id: str
    last_updated: str
    prices: List[Price]


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Bem-vindo ao Historico de Preços de Jogos API",
        "endpoints": [
            "/prices - Retorna o histórico de preços de todos os jogos",
            "/prices/shop/{shop_id} - Retorna o preço mais recente de um jogo específico",
        ],
    }


@app.get("/prices", response_model=PriceHistoryResponse, tags=["Prices"])
async def get_all_prices():
    if "error" in price_data:
        raise HTTPException(status_code=404, detail=price_data["error"])
    return price_data

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
            status_code=404, detail=f"Nenhum preço encontrado para a loja com ID {shop_id}"
        )

    return shop_prices


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
