from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.security import create_access_token
from backend.app.schemas.user import UserLogin, UserOut, TokenOut
from backend.app.services.auth_service import authenticate_user, get_current_user
from backend.app.services.audit_service import log_audit_event
from backend.app.models.user import User

router = APIRouter()

@router.post("/login", response_model=TokenOut)
def login(
    login_data: UserLogin,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password."
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        role=user.role,
        expires_delta=access_token_expires
    )

    # Set secure HttpOnly cookie
    response.set_cookie(
        key="retinax_session",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False  # Set True in production over HTTPS
    )

    log_audit_event(
        db=db,
        action="USER_LOGIN",
        user_name=user.full_name,
        user_role=user.role,
        user_id=str(user.id),
        resource_type="User",
        resource_id=str(user.id),
        details={"email": user.email, "role": user.role},
        ip_address=request.client.host if request.client else ""
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/logout")
def logout(
    response: Response,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    response.delete_cookie(key="retinax_session")
    log_audit_event(
        db=db,
        action="USER_LOGOUT",
        user_name=current_user.full_name,
        user_role=current_user.role,
        user_id=str(current_user.id),
        resource_type="User",
        resource_id=str(current_user.id),
        ip_address=request.client.host if request.client else ""
    )
    return {"message": "Successfully logged out."}

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
