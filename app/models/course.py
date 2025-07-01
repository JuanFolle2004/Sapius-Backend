from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .game import Game

class Course(BaseModel):
    id: str
    title: str
    description: str
    createdBy: str
    createdAt: datetime
    folderId: Optional[str]  # can be null
    games: List[Game]
