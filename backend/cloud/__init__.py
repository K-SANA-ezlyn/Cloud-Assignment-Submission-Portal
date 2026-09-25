"""
Cloud services package — the provider-abstraction layer.

Each module exposes ONE interface with two implementations:
  * storage_service.py : LocalStorageProvider | SupabaseStorageProvider
  * auth_service.py    : LocalAuthProvider    | (Supabase Auth mode)
  * database_service.py: engine/session factory for SQLite or Postgres

The rest of the application depends only on `get_storage_provider()` etc.,
so switching cloud vendor = change env vars, not code.
"""

from backend.cloud.storage_service import get_storage_provider
from backend.cloud.auth_service import verify_token, issue_token, hash_password, verify_password

__all__ = [
    "get_storage_provider",
    "verify_token",
    "issue_token",
    "hash_password",
    "verify_password",
]
