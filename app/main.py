from fastapi import FastAPI
from app.routes.user_routes import router as user_router
from app.routes.folder_routes import router as folder_router
from app.firebase.firebase_config import db
from app.routes.course_routes import router as course_router

app = FastAPI()

# Include all routers
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(folder_router, prefix="/folders", tags=["Folders"])
app.include_router(course_router, prefix="/courses", tags=["Courses"])

@app.get("/")
def root():
    return {"message": "DuoAI backend is running!"}

@app.get("/test-firebase")
def test_firebase():
    return {"collections": [col.id for col in db.collections()]}
