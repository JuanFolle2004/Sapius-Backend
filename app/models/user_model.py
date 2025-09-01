from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import date

class User(BaseModel):
    id: str
    email: str
    name: str
    lastname: str
    phone: Optional[str] = None
    birthDate: date
    recentTopics: List[str] = []
    progress: Dict[str, int] = {}
    interests: List[str] = []        # user-defined interests
    playedGameIds: List[str] = []    # track already played games
