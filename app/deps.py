# app/deps.py
from fastapi import Request
from typing import Optional, Dict, Any
from app.config import COOKIE_NAME
from app.security import decode_token

def get_session(request: Request) -> Optional[Dict[str, Any]]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return decode_token(token)

