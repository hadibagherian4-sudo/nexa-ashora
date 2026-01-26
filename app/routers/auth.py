import time
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User, Referee
from ..security import hash_password, verify_password
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
def login(
    request: Request,
    db: Session = Depends(get_db),
    role: str = Form(...),
    phone: str = Form(...),
    nid: str = Form(""),
    password: str = Form(...)
):
    phone = (phone or "").strip()
    nid = (nid or "").strip()

    # user
    if role == "user":
        u = db.query(User).filter(User.phone == phone).first()
        if not u or not verify_password(password, u.password_hash):
            return templates.TemplateResponse("login.html", {"request": request, "error": "کاربر یافت نشد یا رمز اشتباه است."})
        request.session["auth"] = {"role": "user", "phone": u.phone, "name": u.name, "nid": u.nid}
        return RedirectResponse("/", status_code=303)

    # manager (fixed)
    if role == "manager":
        if phone != settings.MANAGER_PHONE or nid != settings.MANAGER_NID or password != settings.MANAGER_PASSWORD:
            return templates.TemplateResponse("login.html", {"request": request, "error": "مشخصات مدیر سامانه اشتباه است."})
        request.session["auth"] = {"role": "manager", "phone": phone, "name": "مدیر سامانه", "nid": nid}
        return RedirectResponse("/", status_code=303)

    # referee
    if role == "referee":
        r = db.query(Referee).filter(Referee.phone == phone, Referee.nid == nid, Referee.is_active == 1).first()
        if not r or not verify_password(password, r.password_hash):
            return templates.TemplateResponse("login.html", {"request": request, "error": "داور یافت نشد یا مشخصات اشتباه است."})
        request.session["auth"] = {"role": "referee", "phone": r.phone, "name": f"{r.first_name} {r.last_name}", "nid": r.nid}
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse("login.html", {"request": request, "error": "نقش نامعتبر است."})

@router.post("/signup")
def signup(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    phone: str = Form(...),
    nid: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...),
):
    phone = (phone or "").strip()
    nid = (nid or "").strip()
    name = (name or "").strip()

    if not name or not phone or not nid or not password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "همه فیلدها الزامی است."})
    if password != password2:
        return templates.TemplateResponse("login.html", {"request": request, "error": "رمز عبور و تکرار آن یکسان نیست."})

    u = db.query(User).filter(User.phone == phone).first()
    if u:
        u.name = name
        u.nid = nid
        u.password_hash = hash_password(password)
    else:
        u = User(phone=phone, name=name, nid=nid, password_hash=hash_password(password), created_ts=time.time())
        db.add(u)
    db.commit()

    return RedirectResponse("/auth/login", status_code=303)

@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/auth/login", status_code=303)
