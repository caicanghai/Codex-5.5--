from app.bot.main import build_application


def test_build_application_wires_handlers():
    app = build_application("123456:ABCDEF")
    # start, help, voice_set, voice_status, voice_delete, speak, voice-sample, text
    handlers = app.handlers[0]
    assert len(handlers) == 8
