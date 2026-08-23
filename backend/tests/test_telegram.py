from bot.main import notify_user_deleted, notify_user_registered, send_admin_message


def test_notify_skips_without_credentials(monkeypatch) -> None:
    monkeypatch.setattr("bot.main.bot_settings.telegram_token", None)
    monkeypatch.setattr("bot.main.bot_settings.admin_telegram_chat_id", None)

    assert send_admin_message("hello") is False
    assert notify_user_registered("someone", 1) is False
    assert notify_user_deleted("someone", 0) is False
