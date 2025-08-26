FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

COPY apps/api/pyproject.toml apps/api/poetry.lock* ./

RUN poetry config virtualenvs.create false

RUN poetry install --no-dev --no-interaction --no-ansi

COPY apps/api/ ./

RUN mkdir -p storage/uploads storage/books storage/temp

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

    
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
