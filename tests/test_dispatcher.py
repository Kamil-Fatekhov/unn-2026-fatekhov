from unittest.mock import Mock

from echo_bot.dispatcher import Dispatcher
from echo_bot.handlers import EchoHandler
from echo_bot.models import Message, Update


def test_dispatches_message_once():
    handler = Mock()
    message = Message(chat_id=123, text="hello")

    Dispatcher(handler).dispatch(Update(update_id=7, message=message))

    handler.handle.assert_called_once_with(message)


def test_update_without_message_is_ignored():
    handler = Mock()

    Dispatcher(handler).dispatch(Update(update_id=8))

    handler.handle.assert_not_called()


def test_dispatcher_and_handler_ignore_non_text_message(messenger):
    Dispatcher(EchoHandler(messenger)).dispatch(
        Update(update_id=9, message=Message(chat_id=123))
    )

    assert messenger.sent == []
