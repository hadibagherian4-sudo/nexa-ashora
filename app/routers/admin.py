import io
from fastapi import APIRouter, Depends, Form
from fastapi.responses import StreamingResponse, RedirectResponse
from sqlalchemy.orm import Session
from openpyxl import Workbook

from ..db import get_db
from ..deps import require_role
from ..models import User, Referee, SubmissionComment, Submission

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/export/users")
def export_users(auth=Depends(require_role("manager")), db: Session = Depends(get_db)):
    wb = Workbook()
    ws = wb.active
    ws.title = "users"
    ws.append(["phone","name","nid","created_ts"])
    for u in db.query(User).all():
        ws.append([u.phone, u.name, u.nid, u.created_ts])
    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)
    return StreamingResponse(bio, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=users.xlsx"})

@router.get("/export/referees")
def export_referees(auth=Depends(require_role("manager")), db: Session = Depends(get_db)):
    wb = Workbook()
    ws = wb.active
    ws.title = "referees"
    ws.append(["first_name","last_name","phone","nid","field","is_active","created_ts"])
    for r in db.query(Referee).all():
        ws.append([r.first_name, r.last_name, r.phone, r.nid, r.field, r.is_active, r.created_ts])
    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)
    return StreamingResponse(bio, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": "attachment; filename=referees.xlsx"})

@router.post("/comment/delete")
def delete_comment(
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    comment_id: str = Form(...)
):
    db.query(SubmissionComment).filter(SubmissionComment.id == comment_id).delete()
    db.commit()
    return RedirectResponse("/", status_code=303)

@router.post("/submission/delete")
def delete_submission(
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    submission_id: str = Form(...)
):
    db.query(Submission).filter(Submission.id == submission_id).delete()
    db.commit()
    return RedirectResponse("/", status_code=303)

@router.post("/submission/to_correction")
def submission_to_correction(
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    submission_id: str = Form(...)
):
    s = db.query(Submission).filter(Submission.id == submission_id).first()
    if s:
        s.status = "correction_needed"
        db.commit()
    return RedirectResponse("/", status_code=303)
