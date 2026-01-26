# app/routers/forum.py
import time
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.deps import get_session
from app.db import db_conn

router = APIRouter(prefix="/forum")
templates = Jinja2Templates(directory="app/templates")

def make_id(prefix: str) -> str:
    return f"{prefix}{int(time.time()*1000)}"

@router.get("", response_class=HTMLResponse)
def forum_page(request: Request):
    s = get_session(request)
    if not s:
        return RedirectResponse("/login", status_code=302)

    conn = db_conn()
    approved = conn.execute("SELECT * FROM forum_posts WHERE status='approved' ORDER BY created_ts DESC").fetchall()
    replies = {}
    for p in approved:
        replies[p["id"]] = conn.execute("SELECT * FROM forum_replies WHERE post_id=? ORDER BY created_ts ASC", (p["id"],)).fetchall()
    conn.close()

    return templates.TemplateResponse("forum.html", {"request": request, "s": s, "posts": approved, "replies": replies})

@router.post("/post")
def add_post(request: Request, text: str = Form(...)):
    s = get_session(request)
    if not s:
        return RedirectResponse("/login", status_code=302)

    if not text.strip():
        return RedirectResponse("/forum", status_code=302)

    conn = db_conn()
    conn.execute("""
        INSERT INTO forum_posts(id,sender_phone,sender_name,sender_role,text,status,created_ts)
        VALUES(?,?,?,?,?,'pending',?)
    """, (make_id("fp"), s["phone"], s["name"], s["role"], text.strip(), time.time()))
    conn.commit()
    conn.close()
    return RedirectResponse("/forum", status_code=302)

@router.post("/reply")
def add_reply(request: Request, post_id: str = Form(...), text: str = Form(...)):
    s = get_session(request)
    if not s or s["role"] != "referee":
        return RedirectResponse("/login", status_code=302)

    if not text.strip():
        return RedirectResponse("/forum", status_code=302)

    conn = db_conn()
    conn.execute("""
        INSERT INTO forum_replies(id,post_id,referee_phone,referee_name,text,created_ts)
        VALUES(?,?,?,?,?,?)
    """, (make_id("fr"), post_id, s["phone"], s["name"], text.strip(), time.time()))
    conn.commit()
    conn.close()
    return RedirectResponse("/forum", status_code=302)

