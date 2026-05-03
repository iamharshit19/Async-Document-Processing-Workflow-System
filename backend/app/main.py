from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

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

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])

@app.get("/")
def root():
    return {"message": "API is running"}
