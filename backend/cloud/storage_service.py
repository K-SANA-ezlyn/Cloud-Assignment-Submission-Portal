"""
storage_service.py — CLOUD OBJECT STORAGE abstraction.

WHY object storage (and not the database or a web-server folder)?
  * Files are unstructured binary blobs; databases are optimised for
    structured queries, not multi-MB streaming payloads.
  * Object stores (S3 / Supabase Storage / GCS) scale to petabytes,
    cost far less, and serve files via signed URLs / CDNs.

Two providers implement the same interface:

  LocalStorageProvider   -> uploads/ folder on disk (zero setup, offline)
  SupabaseStorageProvider-> private Supabase Storage bucket (free tier)

Selected at runtime by the STORAGE_PROVIDER environment variable.
"""

import logging
import os
import uuid
from abc import ABC, abstractmethod

from backend.config import settings

logger = logging.getLogger("portal.storage")


class StorageError(Exception):
    """Raised when the storage backend fails (mapped to HTTP 503 upstream)."""


class StorageProvider(ABC):
    """Interface every storage provider must implement."""

    @abstractmethod
    def upload(self, data: bytes, path: str) -> str:
        """Store bytes at `path`, return the storage path/key."""

    @abstractmethod
    def download(self, path: str) -> bytes:
        """Return the file bytes stored at `path`."""

    @abstractmethod
    def delete(self, path: str) -> None:
        """Remove the object at `path` (best effort)."""

    @abstractmethod
    def health_check(self) -> bool:
        """Cheap probe used by /api/health/storage."""


def build_storage_path(assignment_id: str, student_id: str, attempt_no: int, original_name: str) -> str:
    """
    Deterministic, collision-proof object key:

        submissions/{assignment_id}/{student_id}/{attempt}_{uuid8}_{safe_name}

    * UUID segment prevents overwrites between users.
    * `safe_name` strips directory components (blocks path traversal).
    * Grouping by assignment/student mirrors the docs folder design.
    """
    safe_name = os.path.basename(original_name).replace("\\", "_").replace("/", "_")
    unique = uuid.uuid4().hex[:8]
    return f"submissions/{assignment_id}/{student_id}/{attempt_no}_{unique}_{safe_name}"


class LocalStorageProvider(StorageProvider):
    """Stores files under UPLOAD_DIR — the local stand-in for S3/Supabase."""

    def __init__(self, base_dir: str | None = None):
        self.base_dir = os.path.abspath(base_dir or settings.UPLOAD_DIR)
        os.makedirs(self.base_dir, exist_ok=True)

    def _full(self, path: str) -> str:
        # Defence-in-depth: never escape the uploads root.
        full = os.path.abspath(os.path.join(self.base_dir, path))
        if not full.startswith(self.base_dir + os.sep) and full != self.base_dir:
            raise StorageError("Invalid storage path")
        return full

    def upload(self, data: bytes, path: str) -> str:
        full = self._full(path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        try:
            with open(full, "wb") as fh:
                fh.write(data)
        except OSError as exc:
            logger.error("Local upload failed for %s: %s", path, exc)
            raise StorageError("Upload failed") from exc
        logger.info("Uploaded %s (%d bytes) to local storage", path, len(data))
        return path

    def download(self, path: str) -> bytes:
        full = self._full(path)
        if not os.path.exists(full):
            raise StorageError("Object not found")
        try:
            with open(full, "rb") as fh:
                return fh.read()
        except OSError as exc:
            logger.error("Local download failed for %s: %s", path, exc)
            raise StorageError("Download failed") from exc

    def delete(self, path: str) -> None:
        full = self._full(path)
        try:
            if os.path.exists(full):
                os.remove(full)
        except OSError as exc:
            logger.warning("Local delete failed for %s: %s", path, exc)

    def health_check(self) -> bool:
        try:
            probe = os.path.join(self.base_dir, ".health")
            with open(probe, "w") as fh:
                fh.write("ok")
            os.remove(probe)
            return True
        except OSError:
            return False


class SupabaseStorageProvider(StorageProvider):
    """
    Stores files in a PRIVATE Supabase Storage bucket (free tier).

    Uploads happen server-side with the service-role key, so the bucket
    can stay private — students never get direct write access. Downloads
    go through short-lived signed URLs issued only after authorization.
    """

    def __init__(self):
        if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY):
            raise StorageError("Supabase storage configured without URL/service key")
        self._client = None  # lazily created so local mode never imports it

    def _get_client(self):
        if self._client is None:
            import httpx  # local mode never needs this import

            self._client = httpx.Client(
                base_url=f"{settings.SUPABASE_URL}/storage/v1",
                headers={
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                    "apikey": settings.SUPABASE_SERVICE_KEY,
                },
                timeout=60.0,
            )
        return self._client

    def upload(self, data: bytes, path: str) -> str:
        url = f"/object/{settings.SUPABASE_STORAGE_BUCKET}/{path}"
        resp = self._get_client().post(url, content=data)
        if resp.status_code not in (200, 201):
            logger.error("Supabase upload failed (%s): %s", resp.status_code, resp.text[:300])
            raise StorageError("Cloud upload failed")
        logger.info("Uploaded %s to Supabase bucket", path)
        return path

    def download(self, path: str) -> bytes:
        url = f"/object/{settings.SUPABASE_STORAGE_BUCKET}/{path}"
        resp = self._get_client().get(url)
        if resp.status_code != 200:
            raise StorageError("Object not found in cloud storage")
        return resp.content

    def delete(self, path: str) -> None:
        url = f"/object/{settings.SUPABASE_STORAGE_BUCKET}/{path}"
        try:
            self._get_client().delete(url)
        except Exception as exc:  # best effort cleanup
            logger.warning("Supabase delete failed for %s: %s", path, exc)

    def create_signed_url(self, path: str, expires_in_seconds: int = 300) -> str:
        """Short-lived private URL — handed out ONLY after authorization."""
        url = f"/object/sign/{settings.SUPABASE_STORAGE_BUCKET}/{path}"
        resp = self._get_client().post(url, json={"expiresIn": expires_in_seconds})
        if resp.status_code != 200:
            raise StorageError("Could not create signed URL")
        return f"{settings.SUPABASE_URL}/storage/v1{resp.json()['signedURL']}"

    def health_check(self) -> bool:
        try:
            probe_path = f"health/probe-{uuid.uuid4().hex[:8]}.txt"
            self.upload(b"ok", probe_path)
            self.delete(probe_path)
            return True
        except StorageError:
            return False


_provider: StorageProvider | None = None


def get_storage_provider() -> StorageProvider:
    """Factory: pick the provider once per process based on env vars."""
    global _provider
    if _provider is None:
        if settings.STORAGE_PROVIDER == "supabase":
            _provider = SupabaseStorageProvider()
            logger.info("Storage provider: SUPABASE (cloud)")
        else:
            _provider = LocalStorageProvider()
            logger.info("Storage provider: LOCAL disk")
    return _provider
