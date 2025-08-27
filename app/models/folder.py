from pydantic import BaseModel, Field
from typing import List, Optional

class FolderCreate(BaseModel):
    title: str
    description: str
    prompt: Optional[str] = None
    gameIds: Optional[List[str]] = []

class Folder(BaseModel):
    id: str
    title: str
    description: str
    prompt: Optional[str] = None
    createdBy: str
    createdAt: str  # ✅ store as ISO string
    gameIds: List[str] = Field(default_factory=list)
