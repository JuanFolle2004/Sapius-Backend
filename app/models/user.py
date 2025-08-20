from pydantic import BaseModel, EmailStr, Field, constr, validator
from datetime import date
from typing import Optional

class CourseProgress(BaseModel):
    completedGames: list[int]
    lastAccessed: str  # ISO datetime

class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=80)
    lastname: str = Field(..., min_length=1, max_length=80)
    phone: Optional[str] = Field(None, max_length=32)
    birthDate: date
    password: str = Field(..., min_length=8, max_length=256)
    interests: list[str] = Field(..., min_items=5, max_items=5)

    @validator("email")
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @validator("name", "lastname")
    def strip_names(cls, v: str) -> str:
        v2 = v.strip()
        if not v2:
            raise ValueError("must not be empty")
        return v2
    
    @validator("password")
    def password_strength(cls, v: str) -> str:
        # simple, non-intrusive checks (tune as needed)
        if v.strip() != v:
            raise ValueError("password must not start/end with spaces")
        has_alpha = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_alpha and has_digit):
            raise ValueError("password must include letters and numbers")
        return v
    
    @validator("birthDate")
    def not_in_future(cls, v: date) -> date:
        from datetime import date as _date
        if v > _date.today():
            raise ValueError("birth date cannot be in the future")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str