from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://myuser:mypassword@db:5432/mydb"
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    UPLOAD_DIR: str = "/app/uploads"

    class Config:
        env_file = ".env"

settings = Settings()
