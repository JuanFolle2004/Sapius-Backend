from pydantic import BaseModel
from typing import List
from datetime import datetime

class Game(BaseModel):
    id: str
    order: int
    question: str
    options: List[str]
    correctAnswer: str
    explanation: str
    title: str
    createdAt: datetime
    createdBy: str
    folderId: str
