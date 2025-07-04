from pydantic import BaseModel
from typing import List, Dict
from datetime import date

class User(BaseModel):
    id: str
    email: str
    name: str
    lastname: str
    phone: str
    birth_date: date
    recentTopics: List[str] = []
    progress: Dict[str, int] = {}
