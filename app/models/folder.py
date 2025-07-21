# models/folder.py

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class FolderCreate(BaseModel):
    title: str
    description: str
    gameIds: Optional[List[str]] = []

class Folder(BaseModel):
    id: str
    title: str
    description: str
    createdBy: str
    createdAt: datetime
    gameIds: List[str] = Field(default_factory=list)  # ✅ this line is key
