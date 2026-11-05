import os
import uuid
from pathlib import Path
from backend.app.storage.base import BaseStorageProvider
from backend.app.core.config import settings
from backend.app.core.security import create_access_token

class LocalStorageProvider(BaseStorageProvider):
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or settings.STORAGE_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, storage_key: str) -> Path:
        # Prevent directory traversal attacks
        safe_key = os.path.basename(storage_key)
        target = (self.base_dir / safe_key).resolve()
        if not str(target).startswith(str(self.base_dir.resolve())):
            raise ValueError(f"Illegal path traversal attempt: {storage_key}")
        return target

    def save_file(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        safe_name = os.path.basename(filename).replace(" ", "_")
        key = f"{uuid.uuid4().hex[:12]}_{safe_name}"
        path = self._safe_path(key)
        path.write_bytes(file_bytes)
        return key

    def get_file_bytes(self, storage_key: str) -> bytes:
        path = self._safe_path(storage_key)
        if not path.exists():
            # Check if file exists directly under base_dir (e.g. initial demo documents)
            direct = self.base_dir / storage_key
            if direct.exists():
                return direct.read_bytes()
            raise FileNotFoundError(f"Storage object {storage_key} not found")
        return path.read_bytes()

    def get_download_url(self, storage_key: str, expires_in: int = 3600) -> str:
        # Generates an internal secure authenticated endpoint reference
        return f"{settings.API_V1_STR}/documents/download/{storage_key}"

    def delete_file(self, storage_key: str) -> bool:
        path = self._safe_path(storage_key)
        if path.exists():
            path.unlink()
            return True
        return False
