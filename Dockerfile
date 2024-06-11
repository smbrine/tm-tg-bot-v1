FROM --platform=linux/amd64 python:3.11-bookworm

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && python -m ensurepip --upgrade && pip install --upgrade pip \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY . .

ENV PYTHONPATH=./
ENV PYTHONUNBUFFERED=True
ENV BIND_PORT=$BIND_PORT

EXPOSE $BIND_PORT

CMD ["python", "-m", "app.main"]
