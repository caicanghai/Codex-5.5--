from app.bot.main import build_application


def test_build_application_wires_handlers():
    app = build_application("123456:ABCDEF")
    # start, help, voice_set/status/delete/list/pick/add/remove, speak,
    # channels, channel_status, channel_test, broadcast, sync_on/off,
    # voice-sample, text
    handlers = app.handlers[0]
    assert len(handlers) == 18
    # An error handler must be registered so handler exceptions never go silent.
    assert len(app.error_handlers) >= 1
