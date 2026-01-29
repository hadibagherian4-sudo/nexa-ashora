import time
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..paths import TEMPLATES_DIR
from ..db import get_db
from ..deps import require_login, require_role, status_fa
from ..models import ForumPost, ForumReply

router = APIRouter(prefix="/forum", tags=["forum"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def make_id(prefix: str):
    return f"{prefix}{int(time.time() * 1000)}"


@router.get("")
def forum_page(request: Request, auth=Depends(require_login), db: Session = Depends(get_db)):
    posts = db.query(ForumPost).filter(ForumPost.status == "published").order_by(ForumPost.created_ts.desc()).all()
    return templates.TemplateResponse("forum.html", {"request": request, "auth": auth, "posts": posts, "status_fa": status_fa})


@router.post("/post")
def create_post(
    request: Request,
    auth=Depends(require_role("user")),
    db: Session = Depends(get_db),
    title: str = Form(...),
    body: str = Form(...),
):
    p = ForumPost(
        id=make_id("fp"),
        title=title.strip(),
        body=body.strip(),
        sender_phone=auth["phone"],
        sender_name=auth["name"],
        status="pending",
        created_ts=time.time(),
    )
    db.add(p)
    db.commit()
    return RedirectResponse("/forum", status_code=303)


@router.post("/reply")
def reply(
    request: Request,
    auth=Depends(require_login),
    db: Session = Depends(get_db),
    post_id: str = Form(...),
    body: str = Form(...),
):
    r = ForumReply(
        id=make_id("fr"),
        post_id=post_id,
        body=body.strip(),
        sender_phone=auth["phone"],
        sender_name=auth["name"],
        created_ts=time.time(),
    )
    db.add(r)
    db.commit()
    return RedirectResponse("/forum", status_code=303)
