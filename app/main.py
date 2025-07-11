from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.routes.user_routes import router as user_router
from app.routes.folder_routes import router as folder_router
from app.routes.course_routes import router as course_router
from app.firebase.firebase_config import db

app = FastAPI()

# Allow CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(folder_router, prefix="/folders", tags=["Folders"])
app.include_router(course_router, prefix="/courses", tags=["Courses"])

# Test endpoints
@app.get("/")
def root():
    return {"message": "DuoAI backend is running!"}

@app.get("/test-firebase")
def test_firebase():
    return {"collections": [col.id for col in db.collections()]}

# Swagger UI customization for Bearer token in headers
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="DuoAI",
        version="1.0.0",
        description="Backend for DuoAI with JWT authentication",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", []).append({"BearerAuth": []})
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Apply the custom OpenAPI schema
app.openapi = custom_openapi
