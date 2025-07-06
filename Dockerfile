# Builder stage
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --user --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY main.py .
COPY config.yaml .

# Final stage
FROM python:3.12-slim

# General
ARG ENV
ARG PORT
ARG VERSION
ARG TITLE
ARG DESCRIPTION

# Database
ARG POSTGRES_HOST
ARG POSTGRES_PORT
ARG POSTGRES_DB
ARG POSTGRES_USER
ARG POSTGRES_PASSWORD
ARG DB_POOL_MIN_SIZE
ARG DB_POOL_MAX_SIZE
ARG DB_POOL_MAX_IDLE
ARG DB_POOL_TIMEOUT

WORKDIR /app

RUN adduser --disabled-password --gecos "" --shell /bin/sh app

COPY --from=builder /root/.local /home/app/.local
ENV PATH=/home/app/.local/bin:$PATH

COPY --from=builder /app /app

RUN chown -R app:app /app
USER app

ENV ENV=$ENV \
    PORT=$PORT \
    VERSION=$VERSION \
    TITLE=$TITLE \
    DESCRIPTION=$DESCRIPTION \
    POSTGRES_HOST=$POSTGRES_HOST \
    POSTGRES_PORT=$POSTGRES_PORT \
    POSTGRES_DB=$POSTGRES_DB \
    POSTGRES_USER=$POSTGRES_USER \
    POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    DB_POOL_MIN_SIZE=$DB_POOL_MIN_SIZE \
    DB_POOL_MAX_SIZE=$DB_POOL_MAX_SIZE \
    DB_POOL_MAX_IDLE=$DB_POOL_MAX_IDLE \
    DB_POOL_TIMEOUT=$DB_POOL_TIMEOUT

EXPOSE $PORT

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:$PORT/api/health')" || exit 1

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]