from fastapi import APIRouter, HTTPException
from app.models.folder import Folder
from app.firebase.firebase_config import db
from datetime import datetime

router = APIRouter()

@router.post("/")
def create_folder(folder: Folder):
    folder_data = folder.dict()
    folder_data["createdAt"] = datetime.utcnow().isoformat()
    db.collection("folders").document(folder.id).set(folder_data)
    return {"message": "Folder created successfully"}

@router.get("/{folder_id}")
def get_folder(folder_id: str):
    doc = db.collection("folders").document(folder_id).get()
    if doc.exists:
        return doc.to_dict()
    else:
        raise HTTPException(status_code=404, detail="Folder not found")

@router.get("/")
def list_folders():
    folders = db.collection("folders").stream()
    return [doc.to_dict() for doc in folders]
