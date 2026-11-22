"""Transport-independent messages and updates."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    chat_id: int
    text: str | None = None


@dataclass(frozen=True)
class Update:
    update_id: int
    message: Message | None = None
