# models/folder.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FolderCreate(BaseModel):
    title: str
    description: str
    courseIds: List[str]

class Folder(BaseModel):
    id: str
    title: str
    description: str
    createdBy: str
    createdAt: datetime
    courseIds: List[str]
