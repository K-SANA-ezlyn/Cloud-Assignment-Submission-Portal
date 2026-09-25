"""
database_service.py — CLOUD DATABASE abstraction (documentation module).

The engine/session for both SQLite (local) and Supabase Postgres (cloud)
is created in backend/database.py from DATABASE_URL. This module records
the operational differences and exposes a health probe used by
/api/health/db to demonstrate cloud-database failure handling.
"""

import logging

from sqlalchemy import text

from backend.database import engine

logger = logging.getLogger("portal.db")


def database_health() -> tuple[bool, str]:
    """Cheap round-trip query; returns (healthy, detail)."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "database reachable"
    except Exception as exc:  # noqa: BLE001 — probe must never raise
        logger.error("Database health check failed: %s", exc)
        return False, "database unreachable"
