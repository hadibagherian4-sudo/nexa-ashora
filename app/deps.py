from fastapi import Depends, Request, HTTPException
from sqlalchemy.orm import Session
from .db import get_db
from .models import User, Referee

def get_session_user(request: Request):
    return request.session.get("auth")  # {role, phone, name, nid}

def require_login(request: Request):
    auth = get_session_user(request)
    if not auth:
        raise HTTPException(status_code=401, detail="Not logged in")
    return auth

def require_role(*roles):
    def _inner(auth=Depends(require_login)):
        if auth["role"] not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return auth
    return _inner

def status_fa(s: str) -> str:
    return {
        "pending": "در انتظار بررسی مدیر سامانه",
        "waiting_referee": "ارجاع شده به داور/داوران",
        "waiting_manager": "در انتظار تایید نهایی مدیر",
        "correction_needed": "نیاز به اصلاح",
        "published": "منتشر شده در ویترین دانش",
        "rejected": "عدم تایید",
        "user": "کاربر",
        "referee": "داور تخصصی / نخبگان دانشی",
        "manager": "مدیر سامانه",
    }.get(s, s)

FIELDS = [
    "۱. حوزه معماری و منظر",
    "۲. حوزه فنی و مهندسی",
    "۳. حوزه برنامه‌ریزی و مدیریت پروژه",
    "۴. حوزه کنترل پروژه",
    "۵. حوزه نقشه‌برداری و فتوگرامتری",
    "۶. حوزه بتن",
    "۷. حوزه هوش مصنوعی",
    "۸. حوزه ICT",
    "۹. حوزه نگهداری و ماشین‌آلات (نت)",
    "۱۰. حوزه کنترل کیفیت (QC)",
    "۱۱. حوزه HSSE",
    "۱۲. حوزه BIM",
    "۱۳. حوزه آسفالت",
    "۱۴. حوزه مالی و حسابداری",
]

CONTENT_TYPES = [
    "ایده‌های خلاقانه",
    "نوشتاری",
    "ویدیویی",
    "پادکست یا صوتی",
    "موشن گرافیک",
    "اینفوگرافیک",
    "پوستر",
    "سایر",
]
