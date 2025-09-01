from fastapi import APIRouter, Depends, HTTPException
from app.firebase.firebase_config import db
from app.models.folder import Folder, FolderCreate
from app.models.user_model import User
from app.utils.auth import get_current_user
from typing import List
from datetime import datetime
from uuid import uuid4

router = APIRouter(prefix="/folders", tags=["Folders"])

@router.post("/", response_model=Folder)
def create_folder(folder: FolderCreate, current_user: User = Depends(get_current_user)):
    print("POST /folders by", current_user.id)
    folder_id = str(uuid4())
    created_at = datetime.utcnow().isoformat()

    folder_data = {
        "id": folder_id,  # opcional
        "title": folder.title,
        "description": folder.description,
        "prompt": folder.prompt,
        "createdBy": current_user.id,  # 👈 sub
        "createdAt": created_at,
        "gameIds": []
    }

    db.collection("folders").document(folder_id).set(folder_data)
    return Folder(**folder_data)

@router.get("/", response_model=List[Folder])
def list_folders(current_user: User = Depends(get_current_user)):
    print("GET /folders for", current_user.id)
    folders_ref = db.collection("folders").where("createdBy", "==", current_user.id).stream()
    folders = []
    for doc in folders_ref:
        folder_data = doc.to_dict()
        folder_data["id"] = doc.id
        created_at = folder_data.get("createdAt")
        if hasattr(created_at, "isoformat"):
            folder_data["createdAt"] = created_at.isoformat()
        folders.append(Folder(**folder_data))
    print("found:", len(folders))
    return folders

@router.get("/{folder_id}/with-games")
def get_folder_with_games(folder_id: str, current_user: User = Depends(get_current_user)):
    folder_doc = db.collection("folders").document(folder_id).get()
    if not folder_doc.exists:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_data = folder_doc.to_dict()
    folder_data["id"] = folder_id

    if folder_data.get("createdBy") != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    game_docs = db.collection("games").where("folderId", "==", folder_id).stream()
    games = []
    for doc in game_docs:
        game = doc.to_dict()
        game["id"] = doc.id
        games.append(game)

    created_at = folder_data.get("createdAt")
    if hasattr(created_at, "isoformat"):
        folder_data["createdAt"] = created_at.isoformat()

    return {"folder": folder_data, "games": games}
