FROM python:3.10-slim-bullseye

WORKDIR /app

# Обновляем систему и ставим системные пакеты
RUN apt-get update && apt-get install -y \
    ca-certificates \
    gcc \
    libffi-dev \
    libssl-dev \
    && apt-get clean

# Обновляем pip
RUN pip install --upgrade pip

# Указываем явно где сертификаты
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone


# Копируем файлы проекта
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot /app

# Стартуем
ENTRYPOINT ["bash", "-c", "pybabel compile -d locales -D bot; wait-for-it -s $DB_ADDRESS:3306; python main.py"]

