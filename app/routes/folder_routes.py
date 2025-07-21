from fastapi import APIRouter, Depends, HTTPException
from app.firebase.firebase_config import db
from app.models.folder import Folder, FolderCreate
from app.utils.auth import get_current_user
from app.models.user_model import User
from typing import List
from datetime import datetime
from uuid import uuid4

router = APIRouter()

@router.post("/", response_model=Folder)
def create_folder(folder: FolderCreate, current_user: User = Depends(get_current_user)):
    folder_id = str(uuid4())
    folder_data = {
        "id": folder_id,
        "title": folder.title,
        "description": folder.description,
        "createdBy": current_user.id,
        "createdAt": datetime.utcnow(),
        "gameIds": []
    }

    db.collection("folders").document(folder_id).set(folder_data)
    return Folder(**folder_data)


@router.get("/", response_model=List[Folder])
def list_folders(current_user: User = Depends(get_current_user)):
    user_id = current_user.id
    folders_ref = db.collection("folders").where("createdBy", "==", user_id).stream()
    return [Folder(**doc.to_dict()) for doc in folders_ref]
