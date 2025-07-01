from pydantic import BaseModel
from typing import List
from datetime import datetime

class Folder(BaseModel):
    id: str
    title: str
    description: str
    createdBy: str
    createdAt: datetime
    courseIds: List[str]
