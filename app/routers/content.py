# app/routers/content.py
import time
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.deps import get_session
from app.db import db_conn

router = APIRouter(prefix="/content")
templates = Jinja2Templates(directory="app/templates")

def make_id(prefix: str) -> str:
    return f"{prefix}{int(time.time()*1000)}"

@router.get("/{sid}", response_class=HTMLResponse)
def view_content(request: Request, sid: str):
    s = get_session(request)
    if not s:
        return RedirectResponse("/login", status_code=302)

    conn = db_conn()
    row = conn.execute("SELECT * FROM submissions WHERE id=?", (sid,)).fetchone()
    if row:
        conn.execute("UPDATE submissions SET views=views+1 WHERE id=?", (sid,))
        conn.commit()
        row = conn.execute("SELECT * FROM submissions WHERE id=?", (sid,)).fetchone()

    comments = conn.execute(
        "SELECT * FROM submission_comments WHERE submission_id=? ORDER BY created_ts ASC",
        (sid,)
    ).fetchall()
    conn.close()

    return templates.TemplateResponse("content_view.html", {"request": request, "s": s, "row": row, "comments": comments, "error": ""})

@router.post("/submit")
async def submit_content(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    field: str = Form("عمومی"),
    content_type: str = Form("general"),
    file: UploadFile | None = File(None),
):
    s = get_session(request)
    if not s or s["role"] != "user":
        return RedirectResponse("/login", status_code=302)

    file_name, file_mime, file_bytes = "", "", None
    if file:
        file_name = file.filename or ""
        file_mime = file.content_type or ""
        file_bytes = await file.read()

    sid = make_id("s")
    conn = db_conn()
    conn.execute("""
        INSERT INTO submissions(
            id,title,description,sender_phone,sender_name,sender_nid,suggested_topic_id,field,content_type,
            file_name,file_mime,file_bytes,status,likes,views,knowledge_code,created_ts
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?, 'pending',0,0,'',?)
    """, (
        sid, title.strip(), description.strip(),
        s["phone"], s["name"], s.get("nid",""),
        "", field, content_type,
        file_name, file_mime, file_bytes, time.time()
    ))
    conn.commit()
    conn.close()
    return RedirectResponse("/", status_code=302)

@router.post("/{sid}/like")
def like_toggle(request: Request, sid: str):
    s = get_session(request)
    if not s or s["role"] != "user":
        return RedirectResponse("/login", status_code=302)

    conn = db_conn()
    cur = conn.cursor()
    existing = cur.execute(
        "SELECT 1 FROM submission_likes WHERE submission_id=? AND user_phone=?",
        (sid, s["phone"])
    ).fetchone()

    if existing:
        cur.execute("DELETE FROM submission_likes WHERE submission_id=? AND user_phone=?", (sid, s["phone"]))
    else:
        cur.execute("INSERT INTO submission_likes(submission_id,user_phone,created_ts) VALUES(?,?,?)", (sid, s["phone"], time.time()))

    cnt = cur.execute("SELECT COUNT(*) FROM submission_likes WHERE submission_id=?", (sid,)).fetchone()[0]
    cur.execute("UPDATE submissions SET likes=? WHERE id=?", (cnt, sid))
    conn.commit()
    conn.close()
    return RedirectResponse(f"/content/{sid}", status_code=302)

@router.post("/{sid}/comment")
def add_comment(request: Request, sid: str, text: str = Form(...)):
    s = get_session(request)
    if not s:
        return RedirectResponse("/login", status_code=302)

    if not text.strip():
        return RedirectResponse(f"/content/{sid}", status_code=302)

    conn = db_conn()
    conn.execute("""
        INSERT INTO submission_comments(id,submission_id,user_name,text,created_ts)
        VALUES(?,?,?,?,?)
    """, (make_id("c"), sid, s["name"], text.strip(), time.time()))
    conn.commit()
    conn.close()
    return RedirectResponse(f"/content/{sid}", status_code=302)

