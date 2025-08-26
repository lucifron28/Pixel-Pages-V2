FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY apps/worker/requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY apps/worker/ ./

CMD ["celery", "-A", "worker.main:app", "worker", "--loglevel=info"]
