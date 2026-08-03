"""Runtime model switch: get/set/clear with a fake Redis, and settings fallback."""

from app import runtime


class _FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, k):
        return self.store.get(k)

    def set(self, k, v):
        self.store[k] = v

    def delete(self, k):
        self.store.pop(k, None)


def test_get_model_falls_back_to_settings(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ai_model", "default-model")
    # Redis raises -> fall back to settings.
    monkeypatch.setattr(runtime.cache, "get_client", lambda: (_ for _ in ()).throw(RuntimeError))
    assert runtime.get_model() == "default-model"


def test_set_then_get_and_clear(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ai_model", "default-model")
    fake = _FakeRedis()
    monkeypatch.setattr(runtime.cache, "get_client", lambda: fake)

    assert runtime.set_model("deepseek-chat") is True
    assert runtime.get_model() == "deepseek-chat"  # override wins
    runtime.clear_model()
    assert runtime.get_model() == "default-model"  # back to default


def test_set_empty_rejected(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setattr(runtime.cache, "get_client", lambda: fake)
    assert runtime.set_model("   ") is False
