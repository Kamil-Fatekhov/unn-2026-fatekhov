class TelegramApiError(RuntimeError):
    def __init__(
        self, message: str, *, retryable: bool = False, retry_after: float = 3.0
    ) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.retry_after = retry_after
