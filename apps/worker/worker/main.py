"""Main worker entry point."""

import os
from celery import Celery

# Redis URL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
app = Celery(
    "pixel_pages_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["worker.tasks"]
)

# Configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
)

if __name__ == "__main__":
    app.start()
