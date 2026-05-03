from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import traceback

from .database import engine, Base
from .routes import documents, progress, auth
from .config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

# Create upload directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Async Document Processing API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Catch-all exception handler so 500 errors still include CORS headers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(f"Unhandled error: {exc}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"},
    )

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])

@app.get("/")
def root():
    return {"message": "API is running"}
