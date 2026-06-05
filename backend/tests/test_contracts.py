import json
from pathlib import Path

from fastapi.testclient import TestClient
from jsonschema import validate

from app.main import app
from app.services.binance_stream_parser import BinanceStreamParser

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts" / "schemas"


def load_schema(file_name: str) -> dict:
    schema_path = CONTRACTS_DIR / file_name
    with schema_path.open("r", encoding="utf-8") as schema_file:
        return json.load(schema_file)


def test_trade_tick_matches_contract_v1() -> None:
    parser = BinanceStreamParser()
    event = parser.parse_trade_tick(
        {
            "e": "aggTrade",
            "s": "BTCUSDT",
            "p": "65001.1",
            "q": "0.4",
            "T": 1717502400000,
        }
    )

    schema = load_schema("trade.tick.v1.json")
    validate(instance=event.model_dump(mode="json"), schema=schema)


def test_kline_closed_matches_contract_v1() -> None:
    parser = BinanceStreamParser()
    event = parser.parse_kline(
        {
            "e": "kline",
            "s": "ETHUSDT",
            "k": {
                "i": "1m",
                "t": 1717502400000,
                "T": 1717502459999,
                "o": "3500.0",
                "h": "3510.0",
                "l": "3495.0",
                "c": "3504.5",
                "v": "200.25",
                "x": True,
            },
        }
    )

    schema = load_schema("kline.closed.v1.json")
    validate(instance=event.model_dump(mode="json"), schema=schema)


def test_market_klines_api_matches_contract_v1() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/market/klines",
        params={"symbol": "btcusdt", "interval": "1m", "limit": 5},
    )

    assert response.status_code == 200
    schema = load_schema("api.market.klines.response.v1.json")
    validate(instance=response.json(), schema=schema)
