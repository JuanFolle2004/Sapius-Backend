import os
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

from app.models.user_model import User
from app.firebase.firebase_config import db

# 🔐 Load secrets from .env
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60*24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ FUNCTION: Hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# ✅ FUNCTION: Verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ✅ FUNCTION: Create access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ✅ FUNCTION: Get current user from token
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    print("🔑 Received token:", token)  # Add this line

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("✅ Payload decoded:", payload)  # Add this line
        user_id: str = payload.get("sub")
        if user_id is None:
            print("❌ Missing 'sub' in token")
            raise credentials_exception
    except JWTError as e:
        print("❌ JWTError:", e)
        raise credentials_exception

    user_doc = db.collection("users").document(user_id).get()
    if not user_doc.exists:
        print("❌ No such user in Firebase:", user_id)
        raise credentials_exception

    print("✅ User authenticated:", user_id)
    user_data = user_doc.to_dict()
    user_data["id"] = user_id
    return User(**user_data)

