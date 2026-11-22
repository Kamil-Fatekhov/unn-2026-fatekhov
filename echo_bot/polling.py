"""Long polling, acknowledgements, and recovery from transient failures."""

import logging
import time
from collections.abc import Callable
from urllib.error import URLError

from echo_bot.dispatcher import Dispatcher
from echo_bot.errors import TelegramApiError
from echo_bot.messenger import Messenger

logger = logging.getLogger(__name__)


class LongPolling:
    def __init__(
        self, messenger: Messenger, dispatcher: Dispatcher, timeout: int = 30
    ) -> None:
        self._messenger = messenger
        self._dispatcher = dispatcher
        self._timeout = timeout
        self.offset = 0

    def run_once(self) -> None:
        for update in self._messenger.get_updates(self.offset, self._timeout):
            if update.update_id < self.offset:
                continue
            self._dispatcher.dispatch(update)
            self.offset = update.update_id + 1

    def run(self, sleep: Callable[[float], None] = time.sleep) -> None:
        while True:
            try:
                self.run_once()
            except TelegramApiError as error:
                if not error.retryable:
                    raise
                logger.warning("Temporary Telegram API error; retrying")
                sleep(error.retry_after)
            except (URLError, TimeoutError, ConnectionError):
                # Exception strings may include the bot token; do not log them.
                logger.warning("Connection to Telegram failed; retrying")
                sleep(3)
