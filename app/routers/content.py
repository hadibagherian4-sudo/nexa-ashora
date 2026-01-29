import time
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..paths import TEMPLATES_DIR
from ..db import get_db
from ..deps import require_login, require_role, FIELDS, CONTENT_TYPES, status_fa
from ..models import Submission, SubmissionLike, SubmissionComment

router = APIRouter(prefix="/content", tags=["content"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/{sid}")
def view_content(sid: str, request: Request, auth=Depends(require_login), db: Session = Depends(get_db)):
    s = db.query(Submission).filter(Submission.id == sid).first()
    if not s:
        return RedirectResponse("/", status_code=303)

    s.views = int(s.views or 0) + 1
    db.commit()

    liked = db.query(SubmissionLike).filter(
        SubmissionLike.submission_id == sid,
        SubmissionLike.phone == auth["phone"]
    ).first() is not None

    comments = db.query(SubmissionComment).filter(
        SubmissionComment.submission_id == sid
    ).order_by(SubmissionComment.created_ts.desc()).all()

    return templates.TemplateResponse("content_view.html", {
        "request": request, "auth": auth,
        "s": s, "liked": liked, "comments": comments,
        "FIELDS": FIELDS, "CONTENT_TYPES": CONTENT_TYPES, "status_fa": status_fa
    })


@router.get("/{sid}/file")
def download_file(sid: str, request: Request, auth=Depends(require_login), db: Session = Depends(get_db)):
    s = db.query(Submission).filter(Submission.id == sid).first()
    if not s or not s.file_bytes:
        return RedirectResponse(f"/content/{sid}", status_code=303)

    filename = s.file_name or "file.bin"
    mime = s.file_mime or "application/octet-stream"
    return Response(
        content=s.file_bytes,
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/{sid}/like")
def like(sid: str, request: Request, auth=Depends(require_role("user")), db: Session = Depends(get_db)):
    s = db.query(Submission).filter(Submission.id == sid).first()
    if not s:
        return RedirectResponse("/", status_code=303)

    existing = db.query(SubmissionLike).filter(
        SubmissionLike.submission_id == sid,
        SubmissionLike.phone == auth["phone"]
    ).first()
    if not existing:
        s.likes = int(s.likes or 0) + 1
        db.add(SubmissionLike(
            id=f"l{int(time.time()*1000)}",
            submission_id=sid,
            phone=auth["phone"],
            created_ts=time.time()
        ))
        db.commit()

    return RedirectResponse(f"/content/{sid}", status_code=303)


@router.post("/{sid}/comment")
def comment(sid: str, request: Request, auth=Depends(require_login), db: Session = Depends(get_db), text: str = Depends()):
    # This endpoint is not used in templates currently (kept for future)
    return RedirectResponse(f"/content/{sid}", status_code=303)
