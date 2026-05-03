import os
import json
import ssl
import time
import random
import redis
import google.generativeai as genai
from celery import Celery
from .config import settings
from .database import SessionLocal
from .models import Document, ExtractedData, JobStatus

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure SSL for rediss:// (Upstash) connections
if settings.CELERY_BROKER_URL.startswith("rediss://"):
    celery_app.conf.broker_use_ssl = {"ssl_cert_reqs": ssl.CERT_NONE}
    celery_app.conf.redis_backend_use_ssl = {"ssl_cert_reqs": ssl.CERT_NONE}

redis_client = redis.Redis.from_url(
    settings.REDIS_URL, 
    decode_responses=True,
    ssl_cert_reqs=ssl.CERT_NONE if settings.REDIS_URL.startswith("rediss://") else None
)

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

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

        document.status = JobStatus.PROCESSING
        db.commit()

        publish_progress(document_id, "document_parsing_started")
        time.sleep(1) # Simulate parsing
        publish_progress(document_id, "document_parsing_completed")

        publish_progress(document_id, "field_extraction_started")
        
        # Real-time token streaming using Gemini or Mock
        summary_text = ""
        if settings.GEMINI_API_KEY:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Write a short, professional summary (3-4 sentences) for a generic '{document.filename}' document."
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    summary_text += chunk.text
                    publish_progress(document_id, "token_stream", {"field": "summary", "chunk": chunk.text})
        else:
            # Mock streaming fallback
            words = "This is a fallback summary since no API key was provided. It is streaming in real time to simulate AI generation across the Pub/Sub system.".split(" ")
            for word in words:
                chunk = word + " "
                summary_text += chunk
                publish_progress(document_id, "token_stream", {"field": "summary", "chunk": chunk})
                time.sleep(0.1)

        extracted = ExtractedData(
            document_id=document_id,
            title=f"Extracted {document.filename}",
            category="AI Processed",
            summary=summary_text.strip(),
            keywords=["gemini", "real-time", "streaming"],
            is_finalized=False
        )
        db.add(extracted)
        document.status = JobStatus.COMPLETED
        db.commit()

        publish_progress(document_id, "field_extraction_completed")
        publish_progress(document_id, "job_completed")

    except Exception as exc:
        db.rollback()
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = JobStatus.FAILED
            db.commit()
        publish_progress(document_id, "job_failed", {"error": str(exc)})
        raise self.retry(exc=exc, countdown=10)
    finally:
        db.close()
