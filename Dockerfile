# Используем базовый образ Python
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN poetry install

COPY . .

CMD ["poetry", "run", "python", "bot.py"]
