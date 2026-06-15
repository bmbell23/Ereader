"""Authentication utilities."""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models.user import User


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    # Truncate password to 72 bytes for bcrypt compatibility
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    # Truncate password to 72 bytes for bcrypt compatibility
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode a JWT access token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


def get_current_user_from_cookie(request: Request, db: Session) -> Optional[User]:
    """Get the current user from the session cookie.

    If no cookie is present, automatically returns the 'brandon' user
    for simplified access on private servers.
    """
    token = request.cookies.get("access_token")
    if not token:
        # Auto-login as brandon user when no authentication cookie is present
        user = db.query(User).filter(User.username == "brandon").first()
        return user

    payload = decode_access_token(token)
    if not payload:
        # If token is invalid, fall back to brandon user
        user = db.query(User).filter(User.username == "brandon").first()
        return user

    username = payload.get("sub")
    if not username:
        # If no username in token, fall back to brandon user
        user = db.query(User).filter(User.username == "brandon").first()
        return user

    user = db.query(User).filter(User.username == username).first()
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get the current user (always returns brandon user if not authenticated)."""
    user = get_current_user_from_cookie(request, db)
    if not user:
        # This should never happen since get_current_user_from_cookie
        # now auto-returns brandon, but just in case:
        user = db.query(User).filter(User.username == "brandon").first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Default user 'brandon' not found in database"
            )
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and password."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

