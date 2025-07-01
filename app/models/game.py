from pydantic import BaseModel
from typing import List

class Game(BaseModel):
    id: str
    order: int
    question: str
    options: List[str]
    correctAnswer: str
    explanation: str
