"""Echo text verbatim through the abstract Messenger interface."""

from echo_bot.messenger import Messenger
from echo_bot.models import Message


class EchoHandler:
    def __init__(self, messenger: Messenger) -> None:
        self._messenger = messenger

    def handle(self, message: Message) -> None:
        if message.text is not None:
            self._messenger.send_message(message.chat_id, message.text)
