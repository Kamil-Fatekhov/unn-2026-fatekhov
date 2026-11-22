import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from urllib.parse import parse_qs

from echo_bot.config import Config
from echo_bot.dispatcher import Dispatcher
from echo_bot.handlers import EchoHandler
from echo_bot.polling import LongPolling
from echo_bot.telegram import TelegramMessenger


def test_full_echo_flow_uses_configured_http_server(monkeypatch):
    text = "  Привет 👋\n<b>&</b>  "
    requests = []
    updates = [
        {"update_id": 40, "message": {"chat": {"id": -1001}, "text": text}},
        {
            "update_id": 41,
            "message": {
                "chat": {"id": -1001},
                "photo": [{"file_id": "photo"}],
                "caption": "must not be echoed",
            },
        },
        {
            "update_id": 42,
            "edited_message": {"chat": {"id": -1001}, "text": "must be ignored"},
        },
    ]

    class FakeTelegram(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers["Content-Length"])
            parameters = parse_qs(self.rfile.read(length).decode("utf-8"))
            requests.append((self.path, parameters))
            if self.path == "/custom/api/botfake-token/getUpdates":
                result = updates if parameters.get("offset") == ["0"] else []
            else:
                result = {"message_id": 1}
            body = json.dumps({"ok": True, "result": result}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            pass

    server = HTTPServer(("127.0.0.1", 0), FakeTelegram)
    worker = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
    worker.daemon = True
    worker.start()
    try:
        monkeypatch.setenv("TELEGRAM_TOKEN", "fake-token")
        monkeypatch.setenv(
            "TELEGRAM_BASE_URL",
            f"http://127.0.0.1:{server.server_port}/custom/api/",
        )
        monkeypatch.setenv("NO_PROXY", "127.0.0.1")
        monkeypatch.setenv("no_proxy", "127.0.0.1")
        config = Config.from_env()
        messenger = TelegramMessenger(config.token, config.base_url)
        polling = LongPolling(messenger, Dispatcher(EchoHandler(messenger)), timeout=1)

        polling.run_once()
        polling.run_once()

        assert polling.offset == 43
        assert requests == [
            (
                "/custom/api/botfake-token/getUpdates",
                {"offset": ["0"], "timeout": ["1"], "allowed_updates": ['["message"]']},
            ),
            (
                "/custom/api/botfake-token/sendMessage",
                {"chat_id": ["-1001"], "text": [text]},
            ),
            (
                "/custom/api/botfake-token/getUpdates",
                {
                    "offset": ["43"],
                    "timeout": ["1"],
                    "allowed_updates": ['["message"]'],
                },
            ),
        ]
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
    assert not worker.is_alive()
