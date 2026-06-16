from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=40, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=80)


class UserLogin(BaseModel):
    # Accept either a username or an email in this field.
    identifier: str
    password: str


class UserUpdate(BaseModel):
    """Editable profile fields. All optional; only provided fields change."""

    display_name: str | None = Field(default=None, max_length=80)
    bio: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = Field(default=None, max_length=500)
    region: str | None = Field(default=None, min_length=2, max_length=2)


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    region: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
