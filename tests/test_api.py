import app.api.main as api
from app.pipeline.service import ProcessResult


def _client(monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setattr(api, "ensure_schema", lambda: None)
    return TestClient(api.app)


def test_health_degraded_without_infra(monkeypatch):
    client = _client(monkeypatch)
    r = client.get("/health")
    assert r.status_code == 503


def test_ingest_rejects_bad_scheme(monkeypatch):
    client = _client(monkeypatch)
    r = client.post("/ingest", json={"url": "ftp://nope"})
    assert r.status_code == 400


def test_ingest_success(monkeypatch):
    async def fake_process(url, persist=True):
        return ProcessResult(id=1, url=url, title="T", summary="S", source="url")

    monkeypatch.setattr(api, "process_url", fake_process)
    client = _client(monkeypatch)
    r = client.post("/ingest", json={"url": "https://example.com/a"})
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "T" and body["summary"] == "S" and body["id"] == 1
