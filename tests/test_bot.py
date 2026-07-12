from app.bot.main import build_application


def test_build_application_wires_three_handlers():
    app = build_application("123456:ABCDEF")
    # /start, /help, and the text MessageHandler.
    handlers = app.handlers[0]
    assert len(handlers) == 3
