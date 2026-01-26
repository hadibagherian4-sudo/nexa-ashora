# app/routers/admin.py
import time
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.deps import get_session
from app.db import db_conn
from app.security import hash_pw

router = APIRouter(prefix="/admin")

def require_manager(request: Request):
    s = get_session(request)
    if not s or s["role"] != "manager":
        return None
    return s

@router.post("/forum/moderate")
def moderate_forum(request: Request, post_id: str = Form(...), action: str = Form(...)):
    s = require_manager(request)
    if not s:
        return RedirectResponse("/login", status_code=302)

    status = "approved" if action == "approve" else "rejected"
    conn = db_conn()
    conn.execute("UPDATE forum_posts SET status=? WHERE id=?", (status, post_id))
    conn.commit()
    conn.close()
    return RedirectResponse("/", status_code=302)

@router.post("/referee/add")
def add_referee(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: str = Form(...),
    nid: str = Form(...),
    field: str = Form(...),
    password: str = Form(...),
    is_active: int = Form(1),
):
    s = require_manager(request)
    if not s:
        return RedirectResponse("/login", status_code=302)

    conn = db_conn()
    conn.execute("""
        INSERT INTO referees(phone,first_name,last_name,nid,field,password,is_active,created_ts)
        VALUES(?,?,?,?,?,?,?,?)
        ON CONFLICT(phone) DO UPDATE SET
          first_name=excluded.first_name,
          last_name=excluded.last_name,
          nid=excluded.nid,
          field=excluded.field,
          password=excluded.password,
          is_active=excluded.is_active
    """, (phone.strip(), first_name.strip(), last_name.strip(), nid.strip(), field, hash_pw(password), int(is_active), time.time()))
    conn.commit()
    conn.close()
    return RedirectResponse("/", status_code=302)

