"""Application interface for receiving and sending messages."""

from typing import Protocol

from echo_bot.models import Update


class Messenger(Protocol):
    def get_updates(self, offset: int, timeout: int) -> list[Update]: ...

    def send_message(self, chat_id: int, text: str) -> None: ...
