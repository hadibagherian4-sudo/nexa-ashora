# app/security.py
from jose import jwt, JWTError
from passlib.context import CryptContext
from typing import Optional, Dict, Any
from app.config import JWT_SECRET, JWT_ALG

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_pw(pw: str) -> str:
    return pwd.hash(pw)

def verify_pw(pw: str, hashed: str) -> bool:
    # اگر دیتای قبلی plain بود، این fallback کمک می‌کند
    if hashed and not hashed.startswith("$2"):
        return pw == hashed
    return pwd.verify(pw, hashed)

def create_token(payload: Dict[str, Any]) -> str:
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        return None

