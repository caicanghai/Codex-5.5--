from app.healthcheck_live import presence_report


def test_presence_report_names_only(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "telegram_bot_token", "123:abc")
    monkeypatch.setattr(settings, "fish_audio_api_key", "")
    report = dict(presence_report())
    # Returns (name -> bool) with no secret values anywhere.
    assert report["TELEGRAM_BOT_TOKEN"] is True
    assert report["FISH_AUDIO_API_KEY"] is False
    for name, present in report.items():
        assert isinstance(name, str) and isinstance(present, bool)
