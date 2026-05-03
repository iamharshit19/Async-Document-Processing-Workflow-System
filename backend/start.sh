#!/bin/bash

# Start Celery worker in the background (concurrency=1 to save memory on free tier)
echo "Starting Celery worker..."
celery -A app.worker.celery_app worker --loglevel=info --concurrency=1 &

# Start FastAPI application
echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
