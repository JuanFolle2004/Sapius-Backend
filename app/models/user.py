from pydantic import BaseModel, EmailStr, constr
from datetime import date

class CourseProgress(BaseModel):
    completedGames: list[int]
    lastAccessed: str  # ISO datetime

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    lastname: str
    password: str
    phone: constr(min_length=6, max_length=20)
    birthDate: date

class UserLogin(BaseModel):
    email: EmailStr
    password: str