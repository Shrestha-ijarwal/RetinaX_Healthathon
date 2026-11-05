from backend.app.core.config import settings
from backend.app.storage.base import BaseStorageProvider
from backend.app.storage.local_storage import LocalStorageProvider

def get_storage_provider() -> BaseStorageProvider:
    if settings.STORAGE_BACKEND.lower() == "s3" and settings.AWS_S3_BUCKET:
        from backend.app.storage.s3_storage import S3StorageProvider
        return S3StorageProvider()
    return LocalStorageProvider()

__all__ = ["BaseStorageProvider", "LocalStorageProvider", "get_storage_provider"]
