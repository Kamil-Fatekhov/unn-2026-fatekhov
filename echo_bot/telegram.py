import json
import urllib.error
import urllib.parse
import urllib.request

from echo_bot.errors import TelegramApiError
from echo_bot.models import Message, Update

__all__ = ["TelegramApiError", "TelegramMessenger"]


class TelegramMessenger:
    def __init__(self, token: str, base_url: str) -> None:
        self._url = f"{base_url.rstrip('/')}/bot{token}"

    def _request(
        self, method: str, parameters: dict[str, str | int], timeout: int = 15
    ) -> object:
        request = urllib.request.Request(
            f"{self._url}/{method}",
            data=urllib.parse.urlencode(parameters).encode("utf-8"),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as error:
            status = error.code
            error.close()
            raise TelegramApiError(
                f"Telegram API method {method} failed (HTTP {status})",
                retryable=status == 429 or status >= 500,
            ) from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise TelegramApiError(
                f"Telegram API method {method}: invalid JSON"
            ) from None
        if not isinstance(payload, dict):
            raise TelegramApiError(f"Telegram API method {method}: invalid response")
        if payload.get("ok") is not True:
            code = payload.get("error_code")
            retryable = isinstance(code, int) and (code == 429 or code >= 500)
            parameters_value = payload.get("parameters")
            delay = 3.0
            if isinstance(parameters_value, dict):
                retry_after = parameters_value.get("retry_after")
                if isinstance(retry_after, (int, float)) and retry_after > 0:
                    delay = float(retry_after)
            raise TelegramApiError(
                f"Telegram API method {method} failed",
                retryable=retryable,
                retry_after=delay,
            )
        return payload.get("result")

    def get_updates(self, offset: int, timeout: int) -> list[Update]:
        result = self._request(
            "getUpdates",
            {
                "offset": offset,
                "timeout": timeout,
                "limit": 100,
                "allowed_updates": json.dumps(["message"]),
            },
            timeout=timeout + 10,
        )
        if not isinstance(result, list):
            raise TelegramApiError("getUpdates returned an invalid result")
        updates: list[Update] = []
        for raw in result:
            if not isinstance(raw, dict) or not isinstance(raw.get("update_id"), int):
                raise TelegramApiError("getUpdates returned an invalid update")
            message = None
            raw_message = raw.get("message")
            if isinstance(raw_message, dict):
                chat = raw_message.get("chat")
                if isinstance(chat, dict) and isinstance(chat.get("id"), int):
                    text = raw_message.get("text")
                    message = Message(
                        chat_id=chat["id"],
                        text=text if isinstance(text, str) else None,
                    )
            updates.append(Update(update_id=raw["update_id"], message=message))
        return updates

    def send_message(self, chat_id: int, text: str) -> None:
        self._request("sendMessage", {"chat_id": chat_id, "text": text})
