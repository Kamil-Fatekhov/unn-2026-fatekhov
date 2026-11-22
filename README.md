# Telegram echo bot

Эхо-бот на Python 3.12+ без aiogram и сторонних зависимостей во время работы.
На входящее текстовое сообщение отвечает тем же текстом в тот же чат.
Другие типы сообщений и обновлений игнорирует. Команды, пробелы, переносы строк,
кириллица и символы разметки возвращаются без изменений.

## Установка и запуск

### PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
$env:TELEGRAM_TOKEN = "ваш-токен"
$env:TELEGRAM_BASE_URL = "https://api.telegram.org"
.\.venv\Scripts\python.exe -m echo_bot
```

### Linux / macOS

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
export TELEGRAM_TOKEN='ваш-токен'
export TELEGRAM_BASE_URL='https://api.telegram.org'
python -m echo_bot
```

Также доступен запуск `python main.py`. Для остановки нажмите Ctrl+C.
`TELEGRAM_TOKEN` и `TELEGRAM_BASE_URL` обязательны. В тестирующей системе
передаётся её адрес: клиент отправляет запросы именно на указанный URL,
добавляя `/bot<token>/<method>`. Базовый URL может включать префикс пути.
Переменные прежнего бота `TOKEN` и `TELEGRAM_URL` больше не используются.
Локальный запуск читает окружение процесса; файл `.env` автоматически не загружается.

## Архитектура

Путь сообщения: long polling → dispatcher → echo handler → messenger.

- `echo_bot/config.py`: чтение и проверка конфигурации при запуске.
- `echo_bot/messenger.py`: интерфейс `Messenger`, от которого зависят компоненты.
- `echo_bot/telegram.py`: HTTP-адаптер Telegram Bot API на `urllib`.
- `echo_bot/polling.py`: long polling и управление offset.
- `echo_bot/dispatcher.py`: выбор обработчика входящего обновления.
- `echo_bot/handlers.py`: отправка исходного текста в исходный чат.
- `echo_bot/__main__.py`: создание и соединение компонентов.

Конкретный Telegram-клиент подключается в точке запуска. Тесты могут подставлять
фиктивный `Messenger` без Telegram и настоящего токена. Offset продвигается после
успешной обработки обновления; игнорируемое обновление также считается обработанным.
После неоднозначного сетевого сбоя при отправке ответ может повториться:
гарантия единственной доставки без поддержки идемпотентности API отсутствует.

## Проверки

После установки зависимостей разработки:

| Команда | Действие |
| --- | --- |
| `make install` | Установить проект и инструменты разработки |
| `make run` | Запустить бота |
| `make test` | Запустить pytest |
| `make format-check` | Проверить форматирование Ruff |
| `make format` | Исправить форматирование Ruff |
| `make lint` | Проверить код Ruff |
| `make lint-fix` | Применить исправления линтера |
| `make typecheck` | Проверить типы строгим mypy |
| `make check` | Выполнить все проверки |
| `make docker-build` | Собрать Docker-образ |

В PowerShell можно указать Python виртуального окружения явно:

```powershell
make PYTHON=.venv/Scripts/python.exe check
```

Если GNU Make не установлен, эквивалентные команды:

```sh
python -m ruff format --check .
python -m ruff check .
python -m mypy
python -m pytest -q
```

Три обязательных набора тестов проверяют polling, dispatcher и handler.
Транспорт и конфигурация дополнительно проверяются без настоящего токена.

## Docker

Запустите Docker Engine / Docker Desktop, затем соберите образ:

```sh
docker build -t unn-2026-fatekhov:local .
```

Скопируйте `.env.example` в `.env` и укажите свои значения. Для PowerShell:

```powershell
Copy-Item .env.example .env
```

Для Linux / macOS:

```sh
cp .env.example .env
```

Запуск с передачей конфигурации при старте контейнера:

```sh
docker run --rm --env-file .env unn-2026-fatekhov:local
```

Контейнер работает от непривилегированного пользователя. Секреты не включаются
в образ: Docker-контекст допускает только исходники и метаданные сборки.
Файлы `.env`, `*.env` и старый `set_env.sh` исключены из Git.

## GitHub Actions и сдача

Workflow `.github/workflows/ci.yml` запускает Ruff format/lint, mypy и pytest
для pull request и изменений в `master`. После проверок собирается Docker-образ.
При push в `master`, включая merge pull request, он также публикуется в GHCR:

```text
ghcr.io/kamil-fatekhov/unn-2026-fatekhov:latest
ghcr.io/kamil-fatekhov/unn-2026-fatekhov:<commit-sha>
```

Имя образа приводится к нижнему регистру. Для публикации используется
`GITHUB_TOKEN`; токен бота в GitHub Actions не требуется. Pull request не публикует образ.

Для сдачи остаются внешние шаги:

1. Создать публичный GitHub-репозиторий `unn-2026-fatekhov` с основной веткой
   `master`, загрузить проект и дождаться успешного workflow.
2. В настройках опубликованного пакета GHCR установить видимость Public
   и проверить доступность образа без авторизации.
3. Зарегистрироваться на `test.olegsklyarov.ru` с тем же email, который использовался
   на `bots.olegsklyarov.ru`, и отправить ссылку на Docker-образ в тестирующую систему.
4. После прохождения всех тестов открыть результат кнопкой «Пройден»
   и сделать скриншот окна.
5. Сдать ссылку на публичный репозиторий, ссылку на публичный образ GHCR
   и скриншот успешного результата.

Репозиторий, пакет и регистрация не создаются автоматически при локальном запуске.
