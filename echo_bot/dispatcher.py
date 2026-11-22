from typing import Protocol

from echo_bot.models import Message, Update


class MessageHandler(Protocol):
    def handle(self, message: Message) -> None: ...


class Dispatcher:
    def __init__(self, handler: MessageHandler) -> None:
        self._handler = handler

    def dispatch(self, update: Update) -> None:
        if update.message is not None:
            self._handler.handle(update.message)
