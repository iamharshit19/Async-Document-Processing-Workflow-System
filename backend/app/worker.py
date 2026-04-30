import os
import json
import time
import random
import redis
from celery import Celery
from .config import settings
from .database import SessionLocal
from .models import Document, ExtractedData, JobStatus

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

def publish_progress(document_id: int, event: str, payload: dict = None):
    if payload is None:
        payload = {}
    message = {
        "document_id": document_id,
        "event": event,
        "payload": payload,
        "timestamp": time.time()
    }
    redis_client.publish(f"document_progress_{document_id}", json.dumps(message))

@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, document_id: int):
    publish_progress(document_id, "job_started")
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            publish_progress(document_id, "job_failed", {"reason": "Document not found"})
            return

        # Update status
        document.status = JobStatus.PROCESSING
        db.commit()

        # Step 1: Parsing
        publish_progress(document_id, "document_parsing_started")
        time.sleep(2) # Simulate work
        publish_progress(document_id, "document_parsing_completed")

        # Step 2: Extraction
        publish_progress(document_id, "field_extraction_started")
        time.sleep(3) # Simulate work
        
        # Generate mock extracted data
        extracted = ExtractedData(
            document_id=document_id,
            title=f"Extracted {document.filename}",
            category=random.choice(["Finance", "Legal", "Engineering", "HR"]),
            summary="This is an automatically generated summary from the mock async pipeline.",
            keywords=["async", "workflow", "celery", "test"],
            is_finalized=False
        )
        db.add(extracted)
        document.status = JobStatus.COMPLETED
        db.commit()

        publish_progress(document_id, "field_extraction_completed")
        publish_progress(document_id, "job_completed")

    except Exception as exc:
        db.rollback()
        # Mark as failed
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = JobStatus.FAILED
            db.commit()
        publish_progress(document_id, "job_failed", {"error": str(exc)})
        raise self.retry(exc=exc, countdown=10)
    finally:
        db.close()
