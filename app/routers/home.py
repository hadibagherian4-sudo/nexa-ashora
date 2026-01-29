import time
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from ..paths import TEMPLATES_DIR
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_login, require_role, FIELDS, CONTENT_TYPES, status_fa
from ..models import (
    User, Referee, Topic, Research, Document,
    Submission, SubmissionAssignment, SubmissionLike, SubmissionComment,
    ForumPost, ForumReply
)
from ..security import hash_password

router = APIRouter(tags=["home"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

def make_id(prefix: str):
    return f"{prefix}{int(time.time() * 1000)}"

@router.get("/")
def home(request: Request, auth=Depends(require_login), db: Session = Depends(get_db)):
    role = auth["role"]

    if role == "user":
        published = db.query(Submission).filter(Submission.status == "published").order_by(Submission.created_ts.desc()).all()
        mysubs = db.query(Submission).filter(Submission.sender_phone == auth["phone"]).order_by(Submission.created_ts.desc()).all()
        topics = db.query(Topic).order_by(Topic.created_ts.desc()).all()
        research = db.query(Research).order_by(Research.created_ts.desc()).all()
        return templates.TemplateResponse("home_user.html", {
            "request": request, "auth": auth,
            "FIELDS": FIELDS, "CONTENT_TYPES": CONTENT_TYPES,
            "published": published, "mysubs": mysubs,
            "topics": topics, "research": research, "status_fa": status_fa
        })

    if role == "manager":
        items = db.query(Submission).filter(
            Submission.status.in_(["pending","waiting_referee","waiting_manager","correction_needed"])
        ).order_by(Submission.created_ts.desc()).all()
        refs = db.query(Referee).order_by(Referee.created_ts.desc()).all()
        users = db.query(User).order_by(User.created_ts.desc()).all()
        topics = db.query(Topic).order_by(Topic.created_ts.desc()).all()
        research = db.query(Research).order_by(Research.created_ts.desc()).all()
        docs = db.query(Document).order_by(Document.created_ts.desc()).all()
        pend_posts = db.query(ForumPost).filter(ForumPost.status == "pending").order_by(ForumPost.created_ts.desc()).all()

        return templates.TemplateResponse("home_manager.html", {
            "request": request, "auth": auth,
            "FIELDS": FIELDS, "CONTENT_TYPES": CONTENT_TYPES,
            "items": items, "refs": refs, "users": users,
            "topics": topics, "research": research, "docs": docs,
            "pend_posts": pend_posts, "status_fa": status_fa
        })

    # referee
    tasks = db.query(SubmissionAssignment).filter(
        SubmissionAssignment.referee_phone == auth["phone"]
    ).order_by(SubmissionAssignment.created_ts.desc()).all()

    # load submission for each task
    mapped = []
    for t in tasks:
        s = db.query(Submission).filter(Submission.id == t.submission_id).first()
        mapped.append({"a": t, "s": s})

    return templates.TemplateResponse("home_referee.html", {
        "request": request, "auth": auth,
        "tasks": mapped, "status_fa": status_fa
    })

# ---------- USER: submit content ----------
@router.post("/user/submit")
def user_submit(
    request: Request,
    auth=Depends(require_role("user")),
    db: Session = Depends(get_db),
    title: str = Form(...),
    description: str = Form(""),
    field: str = Form(...),
    content_type: str = Form(...),
    suggested_topic_id: str = Form(""),
    file: Optional[UploadFile] = File(None),
):
    b = file.file.read() if file else None
    mime = file.content_type if file else None
    fname = file.filename if file else None

    s = Submission(
        id=make_id("s"),
        title=title.strip(),
        description=(description or "").strip(),
        sender_phone=auth["phone"],
        sender_name=auth["name"],
        sender_nid=auth["nid"],
        suggested_topic_id=(suggested_topic_id or "").strip() or None,
        field=field,
        content_type=content_type,
        file_name=fname,
        file_mime=mime,
        file_bytes=b,
        status="pending",
        likes=0,
        views=0,
        knowledge_code="",
        created_ts=time.time()
    )
    db.add(s)
    db.commit()
    return RedirectResponse("/", status_code=303)

# ---------- USER: edit after correction_needed ----------
@router.post("/user/submission/{sid}/resubmit")
def user_resubmit(
    sid: str,
    request: Request,
    auth=Depends(require_role("user")),
    db: Session = Depends(get_db),
    title: str = Form(...),
    description: str = Form(""),
    field: str = Form(...),
    content_type: str = Form(...),
    file: Optional[UploadFile] = File(None),
):
    s = db.query(Submission).filter(Submission.id == sid, Submission.sender_phone == auth["phone"]).first()
    if not s:
        return RedirectResponse("/", status_code=303)

    if s.status != "correction_needed":
        return RedirectResponse("/", status_code=303)

    if file:
        s.file_bytes = file.file.read()
        s.file_mime = file.content_type
        s.file_name = file.filename

    s.title = title.strip()
    s.description = (description or "").strip()
    s.field = field
    s.content_type = content_type
    s.status = "pending"
    s.knowledge_code = ""
    db.commit()
    return RedirectResponse("/", status_code=303)

# ---------- MANAGER: create assignment to multiple referees ----------
@router.post("/manager/assign")
def manager_assign(
    request: Request,
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    submission_id: str = Form(...),
    referee_phones: str = Form(...),  # comma separated
):
    s = db.query(Submission).filter(Submission.id == submission_id).first()
    if not s:
        return RedirectResponse("/", status_code=303)

    phones = [x.strip() for x in referee_phones.split(",") if x.strip()]
    for ph in phones:
        r = db.query(Referee).filter(Referee.phone == ph, Referee.is_active == 1).first()
        if not r:
            continue
        a = SubmissionAssignment(
            id=make_id("a"),
            submission_id=s.id,
            referee_phone=r.phone,
            referee_name=f"{r.first_name} {r.last_name}",
            referee_field=r.field,
            decision="waiting_referee",
            feedback="",
            score=0,
            suggested_knowledge_code="",
            reviewed_ts=None,
            created_ts=time.time()
        )
        db.add(a)

    s.status = "waiting_referee"
    db.commit()
    return RedirectResponse("/", status_code=303)

# ---------- REFEREE: review & update status ----------
@router.post("/referee/review")
def referee_review(
    request: Request,
    auth=Depends(require_role("referee")),
    db: Session = Depends(get_db),
    assignment_id: str = Form(...),
    decision: str = Form(...),  # correction_needed/rejected/recommend_publish
    feedback: str = Form(""),
    score: int = Form(0),
    suggested_knowledge_code: str = Form("")
):
    a = db.query(SubmissionAssignment).filter(
        SubmissionAssignment.id == assignment_id,
        SubmissionAssignment.referee_phone == auth["phone"]
    ).first()
    if not a:
        return RedirectResponse("/", status_code=303)

    a.decision = decision
    a.feedback = (feedback or "").strip()
    a.score = int(score or 0)
    a.suggested_knowledge_code = (suggested_knowledge_code or "").strip()
    a.reviewed_ts = time.time()

    s = db.query(Submission).filter(Submission.id == a.submission_id).first()
    if s:
        s.status = "waiting_manager" if decision == "recommend_publish" else decision

    db.commit()
    return RedirectResponse("/", status_code=303)

# ---------- MANAGER: final decision + publish ----------
@router.post("/manager/finalize")
def manager_finalize(
    request: Request,
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    submission_id: str = Form(...),
    action: str = Form(...),  # publish/reject/correction_needed
    knowledge_code: str = Form("")
):
    s = db.query(Submission).filter(Submission.id == submission_id).first()
    if not s:
        return RedirectResponse("/", status_code=303)

    if action == "publish":
        s.status = "published"
        s.knowledge_code = (knowledge_code or "").strip()
    elif action == "reject":
        s.status = "rejected"
    else:
        s.status = "correction_needed"

    db.commit()
    return RedirectResponse("/", status_code=303)

# ---------- MANAGER: create topic/research/doc ----------
@router.post("/manager/topic")
def manager_topic(
    request: Request,
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    title: str = Form(...),
):
    t = Topic(id=make_id("t"), title=title.strip(), created_ts=time.time())
    db.add(t)
    db.commit()
    return RedirectResponse("/", status_code=303)

@router.post("/manager/research")
def manager_research(
    request: Request,
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    title: str = Form(...),
    body: str = Form(""),
):
    r = Research(id=make_id("r"), title=title.strip(), body=(body or "").strip(), created_ts=time.time())
    db.add(r)
    db.commit()
    return RedirectResponse("/", status_code=303)

@router.post("/manager/document")
def manager_document(
    request: Request,
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    title: str = Form(...),
    body: str = Form(""),
):
    d = Document(id=make_id("d"), title=title.strip(), body=(body or "").strip(), created_ts=time.time())
    db.add(d)
    db.commit()
    return RedirectResponse("/", status_code=303)

# ---------- MANAGER: add referee ----------
@router.post("/manager/referee")
def manager_referee(
    request: Request,
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    first_name: str = Form(...),
    last_name: str = Form(...),
    nid: str = Form(...),
    phone: str = Form(...),
    field: str = Form(...),
    password: str = Form(...),
):
    if db.query(Referee).filter(Referee.phone == phone.strip()).first():
        return RedirectResponse("/", status_code=303)

    r = Referee(
        id=make_id("rf"),
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        nid=nid.strip(),
        phone=phone.strip(),
        field=field,
        password_hash=hash_password(password),
        is_active=1,
        created_ts=time.time(),
    )
    db.add(r)
    db.commit()
    return RedirectResponse("/", status_code=303)

# ---------- MANAGER: approve forum post ----------
@router.post("/manager/forum/approve")
def approve_forum_post(
    request: Request,
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    post_id: str = Form(...),
    action: str = Form(...),  # approve/reject
):
    p = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if p:
        p.status = "published" if action == "approve" else "rejected"
        db.commit()
    return RedirectResponse("/", status_code=303)
