from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    UPLOAD_DIR: str
    GEMINI_API_KEY: str
    SECRET_KEY: str
    FRONTEND_URL: str

    class Config:
        env_file = ".env"

settings = Settings()
