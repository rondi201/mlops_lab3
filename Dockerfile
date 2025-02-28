FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        libsm6 \
        libxext6 \
        libglib2.0-0 \
        curl

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt

# Set the entrypoint
CMD ["python", "-m", "src.api"]