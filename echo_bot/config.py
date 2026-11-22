import os
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Config:
    token: str
    base_url: str

    @classmethod
    def from_env(cls) -> "Config":
        token = os.environ.get("TELEGRAM_TOKEN", "").strip()
        base_url = os.environ.get("TELEGRAM_BASE_URL", "").strip().rstrip("/")
        if not token or not base_url:
            raise ValueError("Set TELEGRAM_TOKEN and TELEGRAM_BASE_URL")
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("TELEGRAM_BASE_URL must be an HTTP(S) URL")
        if parsed.query or parsed.fragment or parsed.username or parsed.password:
            raise ValueError(
                "TELEGRAM_BASE_URL must not contain credentials or a query"
            )
        return cls(token=token, base_url=base_url)
