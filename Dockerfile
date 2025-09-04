FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -f /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src
COPY config.json .

RUN mkdir -p /app/data

ENV DOCKER_ENV=1
ENV PYTHONPATH=/app/src

RUN python -c "fromsrc.backend.init_db import init_database; init_database()"

EXPOSE 8282
CMD ["python", "src/api.py"]


