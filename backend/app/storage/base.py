from abc import ABC, abstractmethod
from typing import Optional

class BaseStorageProvider(ABC):
    @abstractmethod
    def save_file(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        """Saves file and returns a storage key."""
        pass

    @abstractmethod
    def get_file_bytes(self, storage_key: str) -> bytes:
        """Retrieves raw bytes from storage."""
        pass

    @abstractmethod
    def get_download_url(self, storage_key: str, expires_in: int = 3600) -> str:
        """Generates a secure download URL."""
        pass

    @abstractmethod
    def delete_file(self, storage_key: str) -> bool:
        """Deletes a file by storage key."""
        pass
