import importlib

import pytest

from echo_bot.config import Config


def test_configuration_uses_required_environment_names(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_BASE_URL", "http://127.0.0.1:8080/api/")
    monkeypatch.setenv("TOKEN", "obsolete-token")
    monkeypatch.setenv("TELEGRAM_URL", "http://obsolete.invalid")

    config = Config.from_env()

    assert config.token == "test-token"
    assert config.base_url.rstrip("/") == "http://127.0.0.1:8080/api"


@pytest.mark.parametrize("missing", ["TELEGRAM_TOKEN", "TELEGRAM_BASE_URL"])
def test_missing_required_configuration_fails_clearly(monkeypatch, missing):
    monkeypatch.setenv("TELEGRAM_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_BASE_URL", "http://localhost:8080")
    monkeypatch.delenv(missing)

    with pytest.raises(ValueError):
        Config.from_env()


@pytest.mark.parametrize("base_url", ["", "localhost:8080", "ftp://localhost"])
def test_invalid_base_url_is_rejected(monkeypatch, base_url):
    monkeypatch.setenv("TELEGRAM_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_BASE_URL", base_url)

    with pytest.raises(ValueError):
        Config.from_env()


def test_importing_entry_points_does_not_require_secrets(monkeypatch):
    for name in ["TELEGRAM_TOKEN", "TELEGRAM_BASE_URL", "TOKEN", "TELEGRAM_URL"]:
        monkeypatch.delenv(name, raising=False)

    import main

    importlib.reload(main)
    importlib.reload(importlib.import_module("echo_bot.__main__"))
