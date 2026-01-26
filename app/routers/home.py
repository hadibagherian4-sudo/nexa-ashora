# app/routers/home.py
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.deps import get_session
from app.db import db_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/start", response_class=HTMLResponse)
def start(request: Request):
    """
    صفحه شروع (Landing)
    اگر کاربر لاگین باشد مستقیم به داشبورد می‌رود.
    """
    s = get_session(request)
    if s:
        return RedirectResponse("/", status_code=302)

    return templates.TemplateResponse("landing.html", {"request": request, "title": "نکسا"})


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    مسیر اصلی سیستم:
    - اگر لاگین نیست -> به /start برود (صفحه شروع)
    - اگر لاگین هست -> بر اساس نقش داشبورد مناسب را نمایش بدهد
    """
    s = get_session(request)
    if not s:
        # به جای /login، اول صفحه شروع
        return RedirectResponse("/start", status_code=302)

    role = s.get("role")

    if role == "user":
        conn = db_conn()
        published = conn.execute(
            "SELECT * FROM submissions WHERE status='published' ORDER BY created_ts DESC"
        ).fetchall()
        mysubs = conn.execute(
            "SELECT * FROM submissions WHERE sender_phone=? ORDER BY created_ts DESC",
            (s["phone"],),
        ).fetchall()
        conn.close()
        return templates.TemplateResponse(
            "home_user.html",
            {"request": request, "s": s, "published": published, "mysubs": mysubs},
        )

    if role == "manager":
        conn = db_conn()
        queue = conn.execute(
            "SELECT * FROM submissions ORDER BY created_ts DESC"
        ).fetchall()
        pend_posts = conn.execute(
            "SELECT * FROM forum_posts WHERE status='pending' ORDER BY created_ts DESC"
        ).fetchall()
        conn.close()
        return templates.TemplateResponse(
            "home_manager.html",
            {"request": request, "s": s, "queue": queue, "pend_posts": pend_posts},
        )

    # referee
    conn = db_conn()
    tasks = conn.execute(
        """
        SELECT a.*, s.title, s.description, s.sender_name, s.sender_phone, s.field, s.content_type, s.status
        FROM submission_assignments a
        JOIN submissions s ON s.id=a.submission_id
        WHERE a.referee_phone=?
        ORDER BY a.created_ts DESC
        """,
        (s["phone"],),
    ).fetchall()
    conn.close()
    return templates.TemplateResponse(
        "home_referee.html", {"request": request, "s": s, "tasks": tasks}
    )
