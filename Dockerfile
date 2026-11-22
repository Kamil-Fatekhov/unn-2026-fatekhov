FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml ./
COPY echo_bot ./echo_bot
RUN python -m pip install . \
    && useradd --create-home --uid 10001 bot

USER bot
CMD ["python", "-m", "echo_bot"]
