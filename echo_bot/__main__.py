import logging

from echo_bot.config import Config
from echo_bot.dispatcher import Dispatcher
from echo_bot.errors import TelegramApiError
from echo_bot.handlers import EchoHandler
from echo_bot.polling import LongPolling
from echo_bot.telegram import TelegramMessenger


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        config = Config.from_env()
    except ValueError as error:
        raise SystemExit(str(error)) from None
    messenger = TelegramMessenger(config.token, config.base_url)
    polling = LongPolling(messenger, Dispatcher(EchoHandler(messenger)))
    try:
        polling.run()
    except KeyboardInterrupt:
        logging.info("Bot stopped")
    except TelegramApiError as error:
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    main()
