from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_endpoint_returns_prometheus_payload() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
    assert "http_requests_total" in response.text


def test_readyz_endpoint_returns_status_key() -> None:
    response = client.get("/readyz")

    assert response.status_code in {200, 503}
    payload = response.json()
    assert "status" in payload
