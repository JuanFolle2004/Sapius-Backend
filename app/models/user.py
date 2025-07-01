from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional
from datetime import datetime

class CourseProgress(BaseModel):
    completedGames: List[int]
    lastAccessed: datetime

class User(BaseModel):
    id: str
    email: EmailStr
    recentTopics: List[str]
    progress: Dict[str, CourseProgress]  # courseId -> progress
