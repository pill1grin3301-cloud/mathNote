import logging
import socket
from collections.abc import Iterator
from contextlib import contextmanager

import httpx

from bot.config import bot_settings

logger = logging.getLogger(__name__)
HTTP_TIMEOUT = httpx.Timeout(15.0)


@contextmanager
def force_ipv4_dns() -> Iterator[None]:
    original = socket.getaddrinfo

    def ipv4_only(
        host: str,
        port: int,
        family: int = 0,
        type: int = 0,
        proto: int = 0,
        flags: int = 0,
    ):
        return original(host, port, socket.AF_INET, type, proto, flags)

    socket.getaddrinfo = ipv4_only
    try:
        yield
    finally:
        socket.getaddrinfo = original


def send_admin_message(text: str) -> bool:
    token = bot_settings.telegram_token
    chat_id = bot_settings.admin_telegram_chat_id
    if not token or chat_id is None:
        logger.warning(
            "Telegram notification skipped: token or admin chat id is missing"
        )
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    client_kwargs: dict = {"timeout": HTTP_TIMEOUT}
    if bot_settings.telegram_proxy:
        client_kwargs["proxy"] = bot_settings.telegram_proxy

    try:
        with force_ipv4_dns(), httpx.Client(**client_kwargs) as client:
            response = client.post(
                url,
                json={"chat_id": chat_id, "text": text},
            )
        if not response.is_success:
            logger.error(
                "Telegram rejected notification: %s %s",
                response.status_code,
                response.text,
            )
            return False
    except httpx.HTTPError:
        logger.exception(
            "Failed to reach Telegram. If Telegram is blocked, set TELEGRAM_PROXY in backend/.env"
        )
        return False
    return True


def notify_user_registered(username: str, total: int) -> bool:
    return send_admin_message(
        f"Новый пользователь зарегистрирован: {username}\nПользователей сейчас: {total}"
    )


def notify_user_deleted(username: str, total: int) -> bool:
    return send_admin_message(
        f"Пользователь удалён: {username}\nПользователей сейчас: {total}"
    )
