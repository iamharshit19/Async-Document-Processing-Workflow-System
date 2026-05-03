import os
import shutil
from abc import ABC, abstractmethod
from fastapi import UploadFile
from .config import settings

class StorageProvider(ABC):
    @abstractmethod
    def save_file(self, filename: str, file: UploadFile) -> str:
        pass

    @abstractmethod
    def get_file_size(self, filepath: str) -> int:
        pass

class LocalFileStorage(StorageProvider):
    def save_file(self, filename: str, file: UploadFile) -> str:
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path
        
    def get_file_size(self, filepath: str) -> int:
        return os.path.getsize(filepath)

# Singleton instance
storage = LocalFileStorage()
