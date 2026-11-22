from unittest.mock import Mock
from urllib.error import URLError

import pytest

from echo_bot.dispatcher import Dispatcher
from echo_bot.errors import TelegramApiError
from echo_bot.handlers import EchoHandler
from echo_bot.models import Message, Update
from echo_bot.polling import LongPolling


def test_empty_poll_preserves_offset_and_passes_timeout(messenger):
    polling = LongPolling(messenger, Dispatcher(EchoHandler(messenger)), timeout=17)

    polling.run_once()
    polling.run_once()

    assert polling.offset == 0
    assert messenger.polls == [(0, 17), (0, 17)]


def test_poll_echoes_text_and_acknowledges_ignored_updates(messenger):
    messenger.batches.append(
        [
            Update(4, Message(99, "Привет\n👋")),
            Update(5, Message(99)),
            Update(6),
        ]
    )
    polling = LongPolling(messenger, Dispatcher(EchoHandler(messenger)))

    polling.run_once()
    polling.run_once()

    assert messenger.sent == [(99, "Привет\n👋")]
    assert polling.offset == 7
    assert messenger.polls == [(0, 30), (7, 30)]


def test_already_processed_updates_are_not_echoed_again(messenger):
    update = Update(4, Message(99, "once"))
    messenger.batches.extend([[update], [update, Update(5, Message(99, "next"))]])
    polling = LongPolling(messenger, Dispatcher(EchoHandler(messenger)))

    polling.run_once()
    polling.run_once()

    assert messenger.sent == [(99, "once"), (99, "next")]
    assert polling.offset == 6


def test_failure_does_not_acknowledge_unprocessed_update(messenger):
    messenger.batches.append([Update(4), Update(5), Update(6)])
    dispatcher = Mock()
    dispatcher.dispatch.side_effect = [None, RuntimeError("handler failed")]
    polling = LongPolling(messenger, dispatcher)

    with pytest.raises(RuntimeError, match="handler failed"):
        polling.run_once()

    assert polling.offset == 5
    assert dispatcher.dispatch.call_count == 2


def test_run_retries_transient_network_failure_without_advancing_offset(messenger):
    dispatcher = Mock()
    messenger.get_updates = Mock(side_effect=[URLError("offline"), KeyboardInterrupt])
    sleep = Mock()
    polling = LongPolling(messenger, dispatcher)

    with pytest.raises(KeyboardInterrupt):
        polling.run(sleep=sleep)

    assert polling.offset == 0
    assert messenger.get_updates.call_count == 2
    sleep.assert_called_once()
    assert sleep.call_args.args[0] > 0
    dispatcher.dispatch.assert_not_called()


def test_run_honors_api_retry_delay(messenger):
    messenger.get_updates = Mock(
        side_effect=[
            TelegramApiError("rate limited", retryable=True, retry_after=8),
            KeyboardInterrupt,
        ]
    )
    sleep = Mock()
    polling = LongPolling(messenger, Mock())

    with pytest.raises(KeyboardInterrupt):
        polling.run(sleep=sleep)

    sleep.assert_called_once_with(8)
    assert polling.offset == 0


def test_run_surfaces_permanent_api_error_without_retry(messenger):
    messenger.get_updates = Mock(side_effect=TelegramApiError("unauthorized"))
    sleep = Mock()

    with pytest.raises(TelegramApiError, match="unauthorized"):
        LongPolling(messenger, Mock()).run(sleep=sleep)

    sleep.assert_not_called()
