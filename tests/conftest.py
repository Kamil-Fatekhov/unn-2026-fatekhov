"""In-memory transport; tests never call the real Telegram API."""

from collections import deque

import pytest

from echo_bot.models import Update


class FakeMessenger:
    def __init__(self) -> None:
        self.batches: deque[list[Update]] = deque()
        self.polls: list[tuple[int, int]] = []
        self.sent: list[tuple[int, str]] = []

    def get_updates(self, offset: int, timeout: int) -> list[Update]:
        self.polls.append((offset, timeout))
        return self.batches.popleft() if self.batches else []

    def send_message(self, chat_id: int, text: str) -> None:
        self.sent.append((chat_id, text))


@pytest.fixture
def messenger() -> FakeMessenger:
    return FakeMessenger()
