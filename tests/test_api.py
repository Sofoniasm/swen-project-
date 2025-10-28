from fastapi.testclient import TestClient
from api import main as api_main


client = TestClient(api_main.app)


def setup_function():
    # Clear in-memory stores before each test
    try:
        api_main.telemetry_store.clear()
        api_main.decision_store.clear()
    except Exception:
        # If stores are not present, ignore (defensive)
        pass


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)
    assert r.json().get("status") == "ok"


def test_telemetry_and_decisions_post_get():
    t = {
        "service": "testsvc",
        "provider": "aws",
        "region": "us-east-1",
        "cpu": 0.12,
        "memory": 0.34,
        "latency_ms": 42,
        "cost_per_min": 0.001,
    }
    r = client.post("/telemetry", json=t)
    assert r.status_code == 200

    r = client.get("/telemetry")
    assert r.status_code == 200
    data = r.json()
    assert any(item.get("service") == "testsvc" for item in data)

    d = {
        "service": "testsvc",
        "current_provider": "aws",
        "recommended_provider": "aws",
        "region": "us-east-1",
        "reason": "unit-test",
    }
    r = client.post("/decisions", json=d)
    assert r.status_code == 200

    r = client.get("/decisions")
    assert r.status_code == 200
    decisions = r.json()
    assert any(item.get("service") == "testsvc" for item in decisions)
