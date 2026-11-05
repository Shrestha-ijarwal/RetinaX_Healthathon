from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

from backend.app.core.config import settings

ph = PasswordHasher()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    return ph.hash(password)

def create_access_token(subject: Union[str, Any], role: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": role,
        "iat": datetime.now(timezone.utc),
        "iss": "retinax-care-auth"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub", "role"]}
        )
        return payload
    except jwt.PyJWTError:
        return None
