FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y \
    build-essential \
    libsm6 \
    libxext6 \
    libglib2.0-0 \
    curl
# # Для работы pyodbc
# unixodbc

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

WORKDIR /app
ADD . .

# Актуализируем базу данных и запустим API
CMD alembic upgrade head && python -m src.api