from pydantic import BaseModel, EmailStr
from typing import List, Dict
from datetime import datetime, date

class CourseProgress(BaseModel):
    completedGames: List[int]
    lastAccessed: datetime

class User(BaseModel):
    id: str
    email: EmailStr
    birth_date: date  # 👈 NEW FIELD
    recentTopics: List[str]
    progress: Dict[str, CourseProgress]  # courseId -> progress

class UserCreate(BaseModel):
    email: EmailStr
    birthDate: date
    recentTopics: List[str] = []

