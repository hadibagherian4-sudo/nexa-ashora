import time
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_login, require_role, status_fa
from ..models import ForumPost, ForumReply

router = APIRouter(prefix="/forum", tags=["forum"])
templates = Jinja2Templates(directory="app/templates")

def make_id(prefix: str):
    return f"{prefix}{int(time.time() * 1000)}"

@router.get("")
def forum_page(request: Request, auth=Depends(require_login), db: Session = Depends(get_db)):
    approved = db.query(ForumPost).filter(ForumPost.status == "approved").order_by(ForumPost.created_ts.desc()).all()
    # preload replies
    replies_map = {}
    for p in approved:
        replies_map[p.id] = db.query(ForumReply).filter(ForumReply.post_id == p.id).order_by(ForumReply.created_ts.asc()).all()

    return templates.TemplateResponse("forum.html", {
        "request": request, "auth": auth,
        "approved": approved, "replies_map": replies_map,
        "status_fa": status_fa
    })

@router.post("/post")
def post_message(request: Request, auth=Depends(require_login), db: Session = Depends(get_db), text: str = Form(...)):
    if text.strip():
        db.add(ForumPost(
            id=make_id("fp"),
            sender_phone=auth["phone"],
            sender_name=auth["name"],
            sender_role=auth["role"],
            text=text.strip(),
            status="pending",
            created_ts=time.time()
        ))
        db.commit()
    return RedirectResponse("/forum", status_code=303)

@router.post("/reply")
def reply_message(
    request: Request,
    auth=Depends(require_role("referee", "manager")),  # مدیر هم دسترسی کامل دارد
    db: Session = Depends(get_db),
    post_id: str = Form(...),
    text: str = Form(...),
):
    if text.strip():
        db.add(ForumReply(
            id=make_id("fr"),
            post_id=post_id,
            referee_phone=auth["phone"],
            referee_name=auth["name"],
            text=text.strip(),
            created_ts=time.time()
        ))
        db.commit()
    return RedirectResponse("/forum", status_code=303)
