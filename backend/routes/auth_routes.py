"""
auth_routes.py — AUTHENTICATION endpoints.

POST /api/auth/register  create STUDENT or (invite-gated) TEACHER account
POST /api/auth/login     exchange credentials for a JWT access token
POST /api/auth/logout    stateless logout (client discards the token)
GET  /api/auth/me        who am I? (validates the token)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.cloud.auth_service import hash_password, issue_token, verify_password
from backend.config import settings
from backend.database import get_db
from backend.models import User, UserRole
from backend.schemas.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from backend.utils.security import CurrentUser

logger = logging.getLogger("portal.auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new account.

    * STUDENT: open registration (dummy demo accounts welcome).
    * TEACHER: requires TEACHER_INVITE_CODE — demonstrates that role
      assignment is a privileged operation, not a client-side choice.
    """
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    role = UserRole(payload.role)
    if role is UserRole.TEACHER:
        if not payload.invite_code or payload.invite_code != settings.TEACHER_INVITE_CODE:
            logger.warning("Teacher registration blocked: invalid invite code")
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid or missing teacher invite code")

    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Registered %s account for %s", role.value, email)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Verify credentials and issue a signed JWT access token."""
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()

    # Same generic message for unknown email / wrong password (no user enumeration).
    if user is None or not verify_password(payload.password, user.password_hash):
        logger.warning("Failed login attempt for %s", email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    token = issue_token(user.id, user.role.value if isinstance(user.role, UserRole) else str(user.role), user.email)
    logger.info("Login OK for %s (%s)", email, user.role.value)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout")
def logout(current: CurrentUser):
    """
    Stateless JWT logout: the server cannot 'un-sign' a token, so the
    client deletes it. (Production systems add short token lifetimes or
    a revocation list — documented in docs/security.md.)
    """
    return {"detail": f"Logged out. Discard your token, {current.name}."}


@router.get("/me", response_model=UserOut)
def me(current: CurrentUser):
    """Returns the authenticated user — the frontend calls this on boot."""
    return current
