from fastapi import APIRouter, HTTPException, Depends
from app.models.user_model import User
from app.models.user import UserCreate, UserLogin
from app.firebase.firebase_config import db
from uuid import uuid4
from datetime import date
from passlib.context import CryptContext
from app.utils.auth import create_access_token
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

@router.post("", response_model=User)
def create_user(user: UserCreate):
    if db.collection("users").where("email", "==", user.email).get():
        raise HTTPException(status_code=400, detail="Email already registered")

    if user.birthDate > date.today():
        raise HTTPException(status_code=400, detail="Invalid birth date")

    user_id = str(uuid4())
    hashed_password = hash_password(user.password)

    user_dict = {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "lastname": user.lastname,
        "phone": user.phone,
        "birth_date": user.birthDate.isoformat(),
        "recentTopics": [],
        "progress": {},
        "hashed_password": hashed_password,
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

    token = create_access_token({"sub": user_data["id"]})

    return {"access_token": token, "token_type": "bearer"}