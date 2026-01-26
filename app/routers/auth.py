# app/routers/auth.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import COOKIE_NAME, COOKIE_SECURE, MANAGER_PHONE, MANAGER_NID, MANAGER_PASSWORD
from app.db import db_conn, now_ts
from app.security import create_token, hash_pw, verify_pw

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def normalize(x: str) -> str:
    return (x or "").strip().replace(" ", "")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})


@router.post("/login")
def do_login(
    request: Request,
    role: str = Form(...),
    phone: str = Form(...),
    nid: str = Form(""),
    password: str = Form(...),
):
    p = normalize(phone)
    n = normalize(nid)

    if role == "manager":
        if not (MANAGER_PHONE and MANAGER_NID and MANAGER_PASSWORD):
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "مدیر سامانه تنظیم نشده است (مقادیر ENV خالی است)."},
            )
        if p != normalize(MANAGER_PHONE) or n != normalize(MANAGER_NID) or password != MANAGER_PASSWORD:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "مشخصات مدیر سامانه اشتباه است."},
            )
        token = create_token({"role": "manager", "phone": p, "name": "مدیر سامانه", "nid": MANAGER_NID})

    elif role == "referee":
        conn = db_conn()
        row = conn.execute(
            """
            SELECT first_name,last_name,phone,nid,field,password,is_active
            FROM referees
            WHERE phone=? AND nid=? AND is_active=1
            """,
            (p, n),
        ).fetchone()
        conn.close()
        if not row or not verify_pw(password, row["password"]):
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "داور یافت نشد یا مشخصات ورود اشتباه است."},
            )
        token = create_token(
            {
                "role": "referee",
                "phone": p,
                "name": f"{row['first_name']} {row['last_name']}",
                "nid": row["nid"],
                "field": row["field"],
            }
        )

    else:
        conn = db_conn()
        row = conn.execute("SELECT phone,name,nid,password FROM users WHERE phone=?", (p,)).fetchone()
        conn.close()
        if not row or not verify_pw(password, row["password"]):
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "کاربر یافت نشد یا رمز عبور اشتباه است. در صورت نیاز ثبت‌نام کنید."},
            )
        token = create_token({"role": "user", "phone": p, "name": row["name"], "nid": row["nid"]})

    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )
    return resp


# ✅ صفحه ثبت‌نام جدا
@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": ""})


# ✅ ثبت‌نام کاربر (ارسال فرم)
@router.post("/register")
def do_register(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    nid: str = Form(...),
    password1: str = Form(...),
    password2: str = Form(...),
):
    name_clean = (name or "").strip()
    p = normalize(phone)
    n = normalize(nid)

    if not name_clean:
        return templates.TemplateResponse("register.html", {"request": request, "error": "نام و نام خانوادگی الزامی است."})

    if len(n) != 10 or not n.isdigit():
        return templates.TemplateResponse("register.html", {"request": request, "error": "کد ملی باید ۱۰ رقم باشد."})

    if not (p.startswith("09") and p.isdigit() and len(p) in (11,)):
        return templates.TemplateResponse("register.html", {"request": request, "error": "شماره همراه معتبر نیست."})

    if password1 != password2:
        return templates.TemplateResponse("register.html", {"request": request, "error": "رمز عبور و تکرار آن یکسان نیست."})

    if len(password1) < 6:
        return templates.TemplateResponse("register.html", {"request": request, "error": "رمز عبور باید حداقل ۶ کاراکتر باشد."})

    conn = db_conn()

    # اگر همین شماره قبلاً داور/مدیر بوده، قاطی نشه (اختیاری ولی بهتره)
    # (می‌تونی حذفش کنی اگر دوست داشتی)
    ref = conn.execute("SELECT 1 FROM referees WHERE phone=? OR nid=?", (p, n)).fetchone()
    if ref:
        conn.close()
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "این شماره/کد ملی قبلاً به عنوان داور ثبت شده است. از ورود داور استفاده کنید."},
        )

    conn.execute(
        """
        INSERT INTO users(phone,name,nid,password,created_ts)
        VALUES(?,?,?,?,?)
        ON CONFLICT(phone) DO UPDATE SET
            name=excluded.name,
            nid=excluded.nid,
            password=excluded.password
        """,
        (p, name_clean, n, hash_pw(password1), now_ts()),
    )
    conn.commit()
    conn.close()

    return RedirectResponse("/login", status_code=302)


@router.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie(COOKIE_NAME)
    return resp
