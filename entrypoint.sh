#!/bin/bash

missing=0
while read -r requirement; do
    pkg=$(echo "$requirement" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1)
    if ! pip show "$pkg" > /dev/null 2>&1; then
        missing=1
        break
    fi
done < requirements.txt

if [ $missing -eq 1 ]; then
    pip install -r requirements.txt
fi

# Проверяем наличие переменной окружения SECRET_KEY
if [ -z "$FLASK_SECRET_KEY" ]; then
    echo "SECRET_KEY not found. Generating a new one..."
    FLASK_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    export FLASK_SECRET_KEY
    echo "Generated SECRET_KEY: $FLASK_SECRET_KEY"
fi

# Устанавливаем параметры Gunicorn из переменных окружения или используем значения по умолчанию
GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}
GUNICORN_LOG_LEVEL=${GUNICORN_LOG_LEVEL:-info}
GUNICORN_PORT=${GUNICORN_PORT:-8080}
GUNICORN_ADDR=${GUNICORN_BIND:-[::]}

CACHE_SIZE=${CACHE_SIZE:-1024}
export MEMCACHE_PATH=${MEMCACHE_PATH:-"/tmp/memcached.sock"}
if pgrep -x "memcached" > /dev/null; then
    echo "memcached already started"
else
    memcached -d -u nobody -m $CACHE_SIZE $MEMCACHE_PATH
fi

# Проверяем значение переменной DEBUG
if [ "$DEBUG" = "true" ]; then
    exec gunicorn -w "$GUNICORN_WORKERS" -b "$GUNICORN_ADDR:$GUNICORN_PORT" --reload --log-level=debug app.proxy:app
else
    exec gunicorn -w "$GUNICORN_WORKERS" -b "$GUNICORN_ADDR:$GUNICORN_PORT" --log-level="$GUNICORN_LOG_LEVEL" app.proxy:app
fi
