#!/bin/bash

# Start Celery worker in the background
echo "Starting Celery worker..."
celery -A app.worker.celery_app worker --loglevel=info &

# Start FastAPI application
echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
