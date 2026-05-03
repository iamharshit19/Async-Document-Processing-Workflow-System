import asyncio
import json
import redis.asyncio as aioredis
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from ..config import settings

router = APIRouter()

@router.get("/{id}/stream")
async def stream_progress(id: int, request: Request):

    async def event_generator():
        redis_kwargs = {"decode_responses": True}
        if settings.REDIS_URL.startswith("rediss://"):
            import ssl as _ssl
            redis_kwargs["ssl_cert_reqs"] = _ssl.CERT_NONE
        redis = aioredis.from_url(settings.REDIS_URL, **redis_kwargs)
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"document_progress_{id}")

        try:
            while True:
                if await request.is_disconnected():
                    break
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message is not None:
                 
                    yield {
                        "event": "message",
                        "id": str(id),
                        "data": message["data"]
                    }
                await asyncio.sleep(0.1)
        finally:
            await pubsub.unsubscribe(f"document_progress_{id}")
            await redis.aclose()

    return EventSourceResponse(
        event_generator(),
        headers={"Access-Control-Allow-Origin": "*"}
    )
