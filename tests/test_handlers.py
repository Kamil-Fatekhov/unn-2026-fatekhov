import pytest

from echo_bot.handlers import EchoHandler
from echo_bot.models import Message


@pytest.mark.parametrize(
    "text",
    [
        "Привет 👋",
        "  leading and trailing  ",
        "line 1\nline 2",
        "/start",
        "<b>&</b>",
        "",
    ],
)
def test_echo_preserves_exact_text_and_chat(messenger, text):
    EchoHandler(messenger).handle(Message(chat_id=-100123, text=text))

    assert messenger.sent == [(-100123, text)]


def test_non_text_message_is_ignored(messenger):
    EchoHandler(messenger).handle(Message(chat_id=123))

    assert messenger.sent == []
