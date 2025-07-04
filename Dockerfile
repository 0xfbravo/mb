# Builder stage
FROM python:3.12-slim AS builder

ARG PORT
ARG ENV
ARG SERVICE
ARG VERSION

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --user --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY main.py .

# Final stage
FROM python:3.12-slim

ARG PORT
ARG ENV
ARG SERVICE
ARG VERSION

WORKDIR /app

RUN adduser --disabled-password --gecos "" --shell /bin/sh app

COPY --from=builder /root/.local /home/app/.local
ENV PATH=/home/app/.local/bin:$PATH

COPY --from=builder /app /app

RUN chown -R app:app /app
USER app

ENV ENV=$ENV \
    PORT=$PORT \
    SERVICE=$SERVICE \
    VERSION=$VERSION

EXPOSE $PORT

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:$PORT/api/health')" || exit 1

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]