from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user_model import User
from app.models.user import UserCreate
from app.firebase.firebase_config import db
from uuid import uuid4
from datetime import date
from app.utils.auth import hash_password, verify_password, create_access_token

router = APIRouter()

@router.post("/register", response_model=User)
def create_user(user: UserCreate):
    print("✅ Reached backend register route")
    print("📥 Incoming user data:", user.dict())
    if db.collection("users").where("email", "==", user.email).get():
        raise HTTPException(status_code=400, detail="Email already registered")

    if user.birthDate > date.today():
        raise HTTPException(status_code=400, detail="Invalid birth date")

    user_id = str(uuid4())
    hashed = hash_password(user.password)

    user_dict = {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "lastname": user.lastname,
        "phone": user.phone,
        "birth_date": user.birthDate.isoformat(),
        "recentTopics": [],
        "progress": {},
        "hashed_password": hashed,
        "intrests": user.interests
    }

    db.collection("users").document(user_id).set(user_dict)
    return User(**user_dict)

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    query = db.collection("users").where("email", "==", form_data.username).limit(1).stream()
    user_doc = next(query, None)

    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_data = user_doc.to_dict()

    if not verify_password(form_data.password, user_data["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({
        "sub": user_data["id"],
        "email": user_data["email"],
        "name": user_data["name"],
        "lastName": user_data["lastname"]
    })

    return {"access_token": token, "token_type": "bearer"}

