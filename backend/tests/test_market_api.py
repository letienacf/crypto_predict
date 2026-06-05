from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_klines_success() -> None:
    response = client.get(
        "/api/v1/market/klines",
        params={"symbol": "btcusdt", "interval": "1m", "limit": 10},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert len(payload["data"]) == 10


def test_get_klines_reject_invalid_symbol() -> None:
    response = client.get(
        "/api/v1/market/klines",
        params={"symbol": "BTC_USDT", "interval": "1m", "limit": 10},
    )

    assert response.status_code == 422


def test_get_klines_reject_invalid_interval() -> None:
    response = client.get(
        "/api/v1/market/klines",
        params={"symbol": "btcusdt", "interval": "2m", "limit": 10},
    )

    assert response.status_code == 422
