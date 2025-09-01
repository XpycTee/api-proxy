# Используем более стабильную версию Python
FROM python:3.13-alpine

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию
WORKDIR /opt/proxy

# Устанавливаем системные и Python зависимости
COPY requirements.txt ./
RUN apk update \
    && apk add --no-cache bash gcc libc-dev linux-headers memcached \
    && pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .
RUN chmod +x ./entrypoint.sh

# Указываем порты и монтируемые директории
EXPOSE 8080
VOLUME /opt/proxy/config
VOLUME /opt/proxy/logs

# Используем entrypoint.sh для запуска
ENTRYPOINT ["./entrypoint.sh"]
