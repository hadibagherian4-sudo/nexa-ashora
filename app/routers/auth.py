import time
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from ..paths import TEMPLATES_DIR
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User, Referee
from ..security import hash_password, verify_password
from ..deps import set_session, clear_session
from ..config import settings

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def make_id(prefix: str):
    return f"{prefix}{int(time.time() * 1000)}"


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login(
    request: Request,
    db: Session = Depends(get_db),
    phone: str = Form(...),
    password: str = Form(...),
):
    phone = phone.strip()

    # manager fixed login
    if phone == settings.MANAGER_PHONE and password == settings.MANAGER_PASSWORD:
        set_session(request, {"role": "manager", "phone": phone, "name": "مدیر", "nid": settings.MANAGER_NID})
        return RedirectResponse("/", status_code=303)

    # referee
    r = db.query(Referee).filter(Referee.phone == phone, Referee.is_active == 1).first()
    if r and verify_password(password, r.password_hash):
        set_session(request, {"role": "referee", "phone": r.phone, "name": f"{r.first_name} {r.last_name}", "nid": r.nid})
        return RedirectResponse("/", status_code=303)

    # user
    u = db.query(User).filter(User.phone == phone).first()
    if u and verify_password(password, u.password_hash):
        set_session(request, {"role": "user", "phone": u.phone, "name": u.full_name, "nid": u.nid})
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse("login.html", {"request": request, "error": "شماره یا رمز اشتباه است"})


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
def register(
    request: Request,
    db: Session = Depends(get_db),
    full_name: str = Form(...),
    nid: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
):
    phone = phone.strip()
    if db.query(User).filter(User.phone == phone).first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "این شماره قبلاً ثبت شده"})

    u = User(
        id=make_id("u"),
        full_name=full_name.strip(),
        nid=nid.strip(),
        phone=phone,
        password_hash=hash_password(password),
        created_ts=time.time(),
    )
    db.add(u)
    db.commit()

    set_session(request, {"role": "user", "phone": u.phone, "name": u.full_name, "nid": u.nid})
    return RedirectResponse("/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    clear_session(request)
    return RedirectResponse("/login", status_code=303)
