import time
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..db import get_db
from ..deps import require_login, status_fa
from ..models import Submission, SubmissionLike, SubmissionComment

router = APIRouter(prefix="/content", tags=["content"])
templates = Jinja2Templates(directory="app/templates")

def make_id(prefix: str):
    return f"{prefix}{int(time.time() * 1000)}"

@router.get("/{sid}")
def view_content(sid: str, request: Request, auth=Depends(require_login), db: Session = Depends(get_db)):
    s = db.query(Submission).filter(Submission.id == sid).first()
    if not s:
        return RedirectResponse("/", status_code=303)

    # view++ فقط اینجا
    s.views += 1
    db.commit()

    comments = db.query(SubmissionComment).filter(SubmissionComment.submission_id == sid).order_by(SubmissionComment.created_ts.asc()).all()
    return templates.TemplateResponse("content_view.html", {
        "request": request, "auth": auth, "s": s, "comments": comments, "status_fa": status_fa
    })

@router.get("/{sid}/download")
def download_file(sid: str, request: Request, auth=Depends(require_login), db: Session = Depends(get_db)):
    s = db.query(Submission).filter(Submission.id == sid).first()
    if not s or not s.file_bytes:
        return RedirectResponse(f"/content/{sid}", status_code=303)

    return Response(
        content=s.file_bytes,
        media_type=s.file_mime or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{s.file_name or "file"}"'}
    )

@router.post("/{sid}/like")
def like_toggle(sid: str, request: Request, auth=Depends(require_login), db: Session = Depends(get_db)):
    existing = db.query(SubmissionLike).filter(
        SubmissionLike.submission_id == sid,
        SubmissionLike.user_phone == auth["phone"]
    ).first()

    s = db.query(Submission).filter(Submission.id == sid).first()
    if not s:
        return RedirectResponse("/", status_code=303)

    if existing:
        db.delete(existing)
    else:
        db.add(SubmissionLike(submission_id=sid, user_phone=auth["phone"], created_ts=time.time()))

    db.commit()
    # recount
    cnt = db.query(SubmissionLike).filter(SubmissionLike.submission_id == sid).count()
    s.likes = cnt
    db.commit()

    return RedirectResponse(f"/content/{sid}", status_code=303)

@router.post("/{sid}/comment")
def add_comment(sid: str, request: Request, auth=Depends(require_login), db: Session = Depends(get_db), text: str = Form(...)):
    if text.strip():
        db.add(SubmissionComment(
            id=make_id("c"),
            submission_id=sid,
            user_name=auth["name"],
            text=text.strip(),
            created_ts=time.time()
        ))
        db.commit()
    return RedirectResponse(f"/content/{sid}", status_code=303)
