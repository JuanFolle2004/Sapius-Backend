from fastapi import APIRouter, Depends, HTTPException, Body
from app.firebase.firebase_config import db
from app.models.folder import Folder, FolderCreate
from app.models.user_model import User
from app.utils.auth import get_current_user
from typing import List
from datetime import datetime
from uuid import uuid4

router = APIRouter(prefix="/folders", tags=["Folders"])


# 📌 Create a folder
@router.post("/", response_model=Folder)
def create_folder(folder: FolderCreate, current_user: User = Depends(get_current_user)):
    folder_id = str(uuid4())
    created_at = datetime.utcnow().isoformat()

    folder_data = {
        "id": folder_id,
        "title": folder.title,
        "description": folder.description,
        "prompt": folder.prompt,
        "createdBy": current_user.id,
        "createdAt": created_at,
        "gameIds": []  # ✅ Option B
    }

    db.collection("folders").document(folder_id).set(folder_data)
    return Folder(**folder_data)


# 📌 List user’s folders
@router.get("/", response_model=List[Folder])
def list_folders(current_user: User = Depends(get_current_user)):
    folders_ref = db.collection("folders").where("createdBy", "==", current_user.id).stream()
    folders = []
    for doc in folders_ref:
        folder_data = doc.to_dict()
        folder_data["id"] = doc.id
        created_at = folder_data.get("createdAt")
        if hasattr(created_at, "isoformat"):
            folder_data["createdAt"] = created_at.isoformat()
        folders.append(Folder(**folder_data))
    return folders


# 📌 Get a folder + its games
@router.get("/{folder_id}/with-games")
def get_folder_with_games(folder_id: str, current_user: User = Depends(get_current_user)):
    folder_doc = db.collection("folders").document(folder_id).get()
    if not folder_doc.exists:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_data = folder_doc.to_dict()
    folder_data["id"] = folder_id

    if folder_data.get("createdBy") != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    game_ids = folder_data.get("gameIds", [])
    games = []
    for game_id in game_ids:
        game_doc = db.collection("games").document(game_id).get()
        if game_doc.exists:
            game = game_doc.to_dict()
            game["id"] = game_doc.id
            created_at = game.get("createdAt")
            if hasattr(created_at, "isoformat"):
                game["createdAt"] = created_at.isoformat()
            games.append(game)

    created_at = folder_data.get("createdAt")
    if hasattr(created_at, "isoformat"):
        folder_data["createdAt"] = created_at.isoformat()

    return {"folder": folder_data, "games": games}


# 📌 Update (rename / edit) a folder
@router.put("/update/{folder_id}", response_model=Folder)
def update_folder(folder_id: str, updates: dict = Body(...), current_user: User = Depends(get_current_user)):
    folder_ref = db.collection("folders").document(folder_id)
    doc = folder_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_data = doc.to_dict()
    if folder_data.get("createdBy") != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    folder_ref.update(updates)
    folder_data.update(updates)

    return Folder(**folder_data)


# 📌 Delete a folder and its games
@router.delete("/delete/{folder_id}")
def delete_folder(folder_id: str, current_user: User = Depends(get_current_user)):
    folder_ref = db.collection("folders").document(folder_id)
    doc = folder_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder_data = doc.to_dict()
    if folder_data.get("createdBy") != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Delete games inside folder
    for game_id in folder_data.get("gameIds", []):
        db.collection("games").document(game_id).delete()

    # Delete folder itself
    folder_ref.delete()

    return {"success": True, "message": "Folder and its games deleted"}
