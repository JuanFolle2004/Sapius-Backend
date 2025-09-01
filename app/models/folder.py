from pydantic import BaseModel, Field
from typing import List, Optional

class FolderCreate(BaseModel):
    title: str
    description: Optional[str] = None
    prompt: Optional[str] = None

class FolderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None

class Folder(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    prompt: Optional[str] = None
    createdBy: str
    createdAt: str  # store as ISO string
    gameIds: List[str] = Field(default_factory=list)
