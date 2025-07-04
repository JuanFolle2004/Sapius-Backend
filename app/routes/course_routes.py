from fastapi import APIRouter, HTTPException
from app.models.course import Course
from app.firebase.firebase_config import db
from datetime import datetime
from google.cloud import firestore  # Needed for ArrayUnion


router = APIRouter()

@router.post("/")
def create_course(course: Course):
    course_data = course.dict()
    course_data["createdAt"] = datetime.utcnow().isoformat()

    # Save course to Firestore
    db.collection("courses").document(course.id).set(course_data)

    # Optionally update folder it belongs to
    if course.folderId:
        folder_ref = db.collection("folders").document(course.folderId)
        folder_doc = folder_ref.get()
        if folder_doc.exists:
            folder_ref.update({
                "courseIds": firestore.ArrayUnion([course.id])
            })
        else:
            raise HTTPException(status_code=404, detail="Folder not found")

    return {"message": "Course created successfully"}

@router.get("/{course_id}")
def get_course(course_id: str):
    doc = db.collection("courses").document(course_id).get()
    if doc.exists:
        return doc.to_dict()
    else:
        raise HTTPException(status_code=404, detail="Course not found")

@router.get("/")
def list_courses():
    courses = db.collection("courses").stream()
    return [doc.to_dict() for doc in courses]
