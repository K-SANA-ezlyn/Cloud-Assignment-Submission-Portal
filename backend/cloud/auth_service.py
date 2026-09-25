"""
auth_service.py — CLOUD AUTHENTICATION abstraction.

  local mode    : bcrypt password hashing + JWT access tokens (issued by us)
  cloud mode    : Supabase Auth manages users; we verify its JWTs locally

Authentication answers "Who are you?" — authorization ("What may you
do?") is enforced by FastAPI dependencies in backend/utils/security.py.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from backend.config import settings

logger = logging.getLogger("portal.auth")

# passlib bcrypt context (bcrypt 4.x safe)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --------------------------------------------------------------------------
# Password hashing (local mode; Supabase Auth mode delegates this upstream)
# --------------------------------------------------------------------------
def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    return pwd_context.verify(plain, hashed)


# --------------------------------------------------------------------------
# Token issuing / verification
# --------------------------------------------------------------------------
def issue_token(user_id: str, role: str, email: str) -> str:
    """Create a signed JWT access token (local auth mode)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": uuid.uuid4().hex,          # unique token id — good audit practice
        "iss": "assignment-portal",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> dict[str, Any]:
    """
    Verify a token and return its claims.

    local mode    : verify our own HS256 signature + expiry
    cloud mode    : verify a Supabase-issued JWT using the service JWT
                    secret (HS256) or project JWKS (RS256, not shown here)
    Raises jwt.PyJWTError subclasses on any failure.
    """
    if settings.AUTH_PROVIDER == "supabase":
        return jwt.decode(
            token,
            settings.SUPABASE_SERVICE_KEY,
            algorithms=["HS256"],
            options={"verify_aud": False},
            issuer="supabase",
        )
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={"require": ["exp", "sub"]},
    )
