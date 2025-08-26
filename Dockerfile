FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y \
    curl

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

WORKDIR /app
ADD . .

# Актуализируем базу данных и запустим API
CMD alembic upgrade head && python -m src.api