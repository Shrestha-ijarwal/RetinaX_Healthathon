from typing import Optional
from pydantic import ConfigDict, BaseModel, EmailStr

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    username: str
    role: str
    full_name: str
    title: Optional[str] = ""
    facility: Optional[str] = ""
    registration_number: Optional[str] = ""
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class TokenOut(BaseModel):
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserOut

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    title: Optional[str] = None
    facility: Optional[str] = None
