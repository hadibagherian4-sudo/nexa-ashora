import time
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
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
templates = Jinja2Templates(directory="app/templates")

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
    file: UploadFile | None = File(None),
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
    file: UploadFile | None = File(None),
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
    final_status: str = Form(...),  # published/correction_needed/rejected/waiting_manager
    knowledge_code: str = Form("")
):
    s = db.query(Submission).filter(Submission.id == submission_id).first()
    if not s:
        return RedirectResponse("/", status_code=303)

    if final_status == "published":
        if not (knowledge_code or "").strip():
            # بدون پیام خطا در UI ساده نگه داشتیم
            return RedirectResponse("/", status_code=303)
        s.status = "published"
        s.knowledge_code = knowledge_code.strip()
    else:
        s.status = final_status

    db.commit()
    return RedirectResponse("/", status_code=303)

# ---------- MANAGER: add/edit referee ----------
@router.post("/manager/referee/upsert")
def manager_referee_upsert(
    request: Request,
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: str = Form(...),
    nid: str = Form(...),
    field: str = Form(...),
    password: str = Form(...),
    is_active: int = Form(1)
):
    r = db.query(Referee).filter(Referee.phone == phone).first()
    if r:
        r.first_name = first_name.strip()
        r.last_name = last_name.strip()
        r.nid = nid.strip()
        r.field = field
        r.password_hash = hash_password(password)
        r.is_active = 1 if int(is_active) else 0
    else:
        r = Referee(
            phone=phone.strip(),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            nid=nid.strip(),
            field=field,
            password_hash=hash_password(password),
            is_active=1 if int(is_active) else 0,
            created_ts=time.time()
        )
        db.add(r)
    db.commit()
    return RedirectResponse("/", status_code=303)

@router.post("/manager/referee/delete")
def manager_referee_delete(
    request: Request,
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    phone: str = Form(...),
):
    db.query(Referee).filter(Referee.phone == phone).delete()
    db.commit()
    return RedirectResponse("/", status_code=303)

# ---------- MANAGER: topic/research/doc add ----------
@router.post("/manager/topic/add")
def manager_topic_add(
    request: Request,
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    title: str = Form(...),
    field: str = Form(...),
    description: str = Form(""),
    file: UploadFile | None = File(None),
):
    t = Topic(
        id=make_id("top"),
        title=title.strip(),
        field=field,
        description=(description or "").strip(),
        file_name=file.filename if file else None,
        file_bytes=file.file.read() if file else None,
        created_ts=time.time()
    )
    db.add(t)
    db.commit()
    return RedirectResponse("/", status_code=303)

@router.post("/manager/research/add")
def manager_research_add(
    request: Request,
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    title: str = Form(...),
    field: str = Form(...),
    summary: str = Form(""),
    file: UploadFile | None = File(None),
):
    r = Research(
        id=make_id("res"),
        title=title.strip(),
        field=field,
        summary=(summary or "").strip(),
        file_name=file.filename if file else None,
        file_bytes=file.file.read() if file else None,
        created_ts=time.time()
    )
    db.add(r)
    db.commit()
    return RedirectResponse("/", status_code=303)

@router.post("/manager/document/add")
def manager_document_add(
    request: Request,
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    title: str = Form(...),
    file: UploadFile = File(...),
):
    d = Document(
        id=make_id("doc"),
        title=title.strip(),
        file_name=file.filename,
        file_bytes=file.file.read(),
        created_ts=time.time()
    )
    db.add(d)
    db.commit()
    return RedirectResponse("/", status_code=303)

# ---------- MANAGER: forum approve/reject ----------
@router.post("/manager/forum/moderate")
def manager_forum_moderate(
    request: Request,
    auth=Depends(require_role("manager")),
    db: Session = Depends(get_db),
    post_id: str = Form(...),
    action: str = Form(...),  # approved/rejected
):
    p = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if p:
        p.status = action
        db.commit()
    return RedirectResponse("/", status_code=303)
