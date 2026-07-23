"""API smoke tests (ADR-0010, 10e) — correct shape and status."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_shape():
    r = client.get("/api/metrics")
    assert r.status_code == 200
    body = r.json()
    for key in ("fy_summary", "monthly", "seasonality", "cost_structure", "product_mix"):
        assert key in body and isinstance(body[key], list) and body[key]


def test_bridges():
    r = client.get("/api/bridges")
    assert r.status_code == 200
    entities = {b["entity"] for b in r.json()}
    assert entities == {"AU", "NZ"}


def test_findings():
    r = client.get("/api/findings")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] in ("offline", "live")
    assert body["dropped"] == 0  # offline findings are all grounded
    ids = {f["finding_id"] for f in body["findings"]}
    assert "F-NZ-MARGIN" in ids
    # First finding is highest materiality.
    assert body["findings"][0]["materiality"] == "High"
