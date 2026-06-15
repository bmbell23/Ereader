"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import timedelta

from ..database import get_db
from ..models.user import User
from ..auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_user_from_cookie,
    get_current_user,
    verify_password,
)
from ..config import settings

router = APIRouter()

# Setup templates
templates = Jinja2Templates(directory=str(settings.templates_dir))


class UserLogin(BaseModel):
    """User login schema."""
    username: str
    password: str


class PasswordChange(BaseModel):
    """Password change schema."""
    current_password: str
    new_password: str


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "title": "Login - GreatReads",
        }
    )


@router.post("/api/auth/login")
async def login(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Login user."""
    user = authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.access_token_expire_minutes * 60,
        samesite="lax",
        path="/"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
        }
    }


@router.post("/api/auth/logout")
async def logout(response: Response):
    """Logout user."""
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Logged out successfully"}


@router.get("/api/auth/me")
async def get_current_user_info(request: Request, db: Session = Depends(get_db)):
    """Get current user info."""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
    }


@router.post("/api/auth/change-password")
async def change_password(
    password_data: PasswordChange,
    request: Request,
    db: Session = Depends(get_db)
):
    """Change user password."""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Verify current password
    if not verify_password(password_data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    user.password_hash = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "Password changed successfully"}

