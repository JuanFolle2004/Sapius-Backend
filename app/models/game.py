from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class Game(BaseModel):
    id: str
    order: int
    title: str
    question: str
    options: List[str]
    correctAnswer: str
    explanation: str
    createdAt: datetime
    createdBy: str
    folderId: Optional[str] = None   # can be "random" for trivia
    topic: Optional[str] = None      # keep optional for safety
    tags: List[str] = Field(default_factory=list)
