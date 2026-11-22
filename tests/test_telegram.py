import io
import json
from unittest.mock import Mock
from urllib.error import HTTPError
from urllib.parse import parse_qs

import pytest

from echo_bot.models import Message, Update
from echo_bot.telegram import TelegramApiError, TelegramMessenger


def mock_response(monkeypatch, payload):
    opener = Mock(return_value=io.BytesIO(json.dumps(payload).encode()))
    monkeypatch.setattr("urllib.request.urlopen", opener)
    return opener


def test_get_updates_uses_configured_endpoint_and_long_poll_timeout(monkeypatch):
    opener = mock_response(
        monkeypatch,
        {
            "ok": True,
            "result": [
                {"update_id": 10, "message": {"chat": {"id": 9}, "text": "Привет"}},
                {"update_id": 11, "callback_query": {}},
            ],
        },
    )
    messenger = TelegramMessenger("fake-token", "http://localhost:9000/custom/")

    updates = messenger.get_updates(offset=7, timeout=30)

    assert updates == [Update(10, Message(9, "Привет")), Update(11)]
    request = opener.call_args.args[0]
    assert request.full_url == "http://localhost:9000/custom/botfake-token/getUpdates"
    assert request.get_method() == "POST"
    parameters = parse_qs(request.data.decode())
    assert parameters["offset"] == ["7"]
    assert parameters["timeout"] == ["30"]
    assert parameters["limit"] == ["100"]
    assert json.loads(parameters["allowed_updates"][0]) == ["message"]
    assert opener.call_args.kwargs["timeout"] > 30


def test_empty_polls_always_include_limit(monkeypatch):
    opener = Mock(
        side_effect=lambda *_args, **_kwargs: io.BytesIO(
            json.dumps({"ok": True, "result": []}).encode()
        )
    )
    monkeypatch.setattr("urllib.request.urlopen", opener)
    messenger = TelegramMessenger("fake-token", "http://test.invalid")

    assert messenger.get_updates(0, 30) == []
    assert messenger.get_updates(0, 30) == []

    assert opener.call_count == 2
    for call in opener.call_args_list:
        parameters = parse_qs(call.args[0].data.decode())
        assert parameters["limit"] == ["100"]
        assert parameters["offset"] == ["0"]


def test_send_message_preserves_unicode_and_omits_parse_mode(monkeypatch):
    opener = mock_response(monkeypatch, {"ok": True, "result": {"message_id": 1}})
    messenger = TelegramMessenger("fake-token", "http://test.invalid")
    text = "  Привет 👋\n<b>&</b>  "

    messenger.send_message(-1001, text)

    request = opener.call_args.args[0]
    assert request.full_url == "http://test.invalid/botfake-token/sendMessage"
    assert parse_qs(request.data.decode()) == {
        "chat_id": ["-1001"],
        "text": [text],
    }
    assert opener.call_args.kwargs["timeout"] > 0


@pytest.mark.parametrize(
    "message",
    [
        {"photo": [{"file_id": "photo"}], "caption": "not echo text"},
        {"sticker": {"file_id": "sticker"}},
        {"document": {"file_id": "document"}},
    ],
)
def test_non_text_payloads_are_not_converted_to_echo_text(monkeypatch, message):
    mock_response(
        monkeypatch,
        {
            "ok": True,
            "result": [{"update_id": 1, "message": {"chat": {"id": 9}, **message}}],
        },
    )

    updates = TelegramMessenger("fake-token", "http://test.invalid").get_updates(0, 30)

    assert updates == [Update(1, Message(9))]


def test_edited_messages_are_ignored(monkeypatch):
    mock_response(
        monkeypatch,
        {
            "ok": True,
            "result": [
                {"update_id": 2, "edited_message": {"chat": {"id": 9}, "text": "edit"}}
            ],
        },
    )

    updates = TelegramMessenger("fake-token", "http://test.invalid").get_updates(0, 30)

    assert updates == [Update(2)]


def test_api_rejection_does_not_expose_token(monkeypatch):
    token = "sensitive-test-token"
    mock_response(
        monkeypatch,
        {"ok": False, "error_code": 401, "description": f"rejected {token}"},
    )

    with pytest.raises(TelegramApiError) as error:
        TelegramMessenger(token, "http://test.invalid").send_message(9, "hello")

    assert token not in str(error.value)


def test_rate_limit_response_carries_server_retry_delay(monkeypatch):
    mock_response(
        monkeypatch,
        {
            "ok": False,
            "error_code": 429,
            "parameters": {"retry_after": 12},
        },
    )

    with pytest.raises(TelegramApiError) as error:
        TelegramMessenger("fake-token", "http://test.invalid").get_updates(0, 30)

    assert error.value.retryable is True
    assert error.value.retry_after == 12


@pytest.mark.parametrize("status,retryable", [(401, False), (429, True), (503, True)])
def test_http_error_is_sanitized_and_classified(monkeypatch, status, retryable):
    body = io.BytesIO(b"sensitive-test-token")
    failure = HTTPError(
        "http://test.invalid/botsensitive-test-token/sendMessage",
        status,
        "sensitive-test-token",
        None,
        body,
    )
    monkeypatch.setattr("urllib.request.urlopen", Mock(side_effect=failure))

    with pytest.raises(TelegramApiError) as error:
        TelegramMessenger("sensitive-test-token", "http://test.invalid").send_message(
            9, "hello"
        )

    assert error.value.retryable is retryable
    assert "sensitive-test-token" not in str(error.value)
    assert body.closed


@pytest.mark.parametrize("result", [None, {}, [None], [{"update_id": "invalid"}]])
def test_malformed_update_result_raises_controlled_error(monkeypatch, result):
    mock_response(monkeypatch, {"ok": True, "result": result})

    with pytest.raises(TelegramApiError):
        TelegramMessenger("fake-token", "http://test.invalid").get_updates(0, 30)
