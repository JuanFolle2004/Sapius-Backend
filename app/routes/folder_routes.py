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
        "prompt": folder.prompt,
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

@router.get("/{folder_id}")
def get_folder_details(folder_id: str, current_user: User = Depends(get_current_user)):
    folder_doc = db.collection("folders").document(folder_id).get()
    if not folder_doc.exists:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_data = folder_doc.to_dict()
    folder_data["id"] = folder_id

    if folder_data["createdBy"] != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Fetch all games in this folder
    game_docs = db.collection("games")\
        .where("folderId", "==", folder_id)\
        .where("createdBy", "==", current_user.id)\
        .stream()

    games = []
    for doc in game_docs:
        data = doc.to_dict()
        data["id"] = doc.id
        games.append(data)

    return {
        "folder": folder_data,
        "games": games
    }


@router.get("/folders/{folder_id}/with-games")
def get_folder_with_games(folder_id: str, current_user: User = Depends(get_current_user)):
    folder_doc = db.collection("folders").document(folder_id).get()
    if not folder_doc.exists:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_data = folder_doc.to_dict()
    folder_data["id"] = folder_id

    if folder_data["createdBy"] != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Fetch games belonging to this folder
    game_docs = db.collection("games")\
        .where("folderId", "==", folder_id)\
        .where("createdBy", "==", current_user.id)\
        .stream()

    games = []
    for doc in game_docs:
        game = doc.to_dict()
        game["id"] = doc.id
        games.append(game)

    return {
        "folder": folder_data,
        "games": games
    }

