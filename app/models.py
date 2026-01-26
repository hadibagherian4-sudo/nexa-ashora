import enum
from sqlalchemy import (
    Column, String, Integer, Float, Text, ForeignKey, LargeBinary, UniqueConstraint
)
from sqlalchemy.orm import relationship
from .db import Base

class Role(str, enum.Enum):
    user = "user"
    referee = "referee"
    manager = "manager"

class SubmissionStatus(str, enum.Enum):
    pending = "pending"
    waiting_referee = "waiting_referee"
    waiting_manager = "waiting_manager"
    correction_needed = "correction_needed"
    rejected = "rejected"
    published = "published"

class ForumStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class User(Base):
    __tablename__ = "users"
    phone = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    nid = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_ts = Column(Float, nullable=False)

class Referee(Base):
    __tablename__ = "referees"
    phone = Column(String, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    nid = Column(String, nullable=False)
    field = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    created_ts = Column(Float, nullable=False)

class Topic(Base):
    __tablename__ = "topics"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    field = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    file_name = Column(String, nullable=True)
    file_bytes = Column(LargeBinary, nullable=True)
    created_ts = Column(Float, nullable=False)

class Research(Base):
    __tablename__ = "research"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    field = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    file_name = Column(String, nullable=True)
    file_bytes = Column(LargeBinary, nullable=True)
    created_ts = Column(Float, nullable=False)

class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_bytes = Column(LargeBinary, nullable=False)
    created_ts = Column(Float, nullable=False)

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)

    sender_phone = Column(String, ForeignKey("users.phone"), nullable=False)
    sender_name = Column(String, nullable=False)
    sender_nid = Column(String, nullable=False)

    suggested_topic_id = Column(String, nullable=True)
    field = Column(String, nullable=False)
    content_type = Column(String, nullable=False)

    file_name = Column(String, nullable=True)
    file_mime = Column(String, nullable=True)
    file_bytes = Column(LargeBinary, nullable=True)

    status = Column(String, nullable=False)  # SubmissionStatus
    likes = Column(Integer, default=0, nullable=False)
    views = Column(Integer, default=0, nullable=False)
    knowledge_code = Column(String, nullable=True)
    created_ts = Column(Float, nullable=False)

    assignments = relationship("SubmissionAssignment", cascade="all, delete-orphan", back_populates="submission")
    comments = relationship("SubmissionComment", cascade="all, delete-orphan", back_populates="submission")
    likes_rel = relationship("SubmissionLike", cascade="all, delete-orphan", back_populates="submission")

class SubmissionAssignment(Base):
    __tablename__ = "submission_assignments"
    id = Column(String, primary_key=True)
    submission_id = Column(String, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)

    referee_phone = Column(String, nullable=False)
    referee_name = Column(String, nullable=False)
    referee_field = Column(String, nullable=False)

    decision = Column(String, nullable=False)  # waiting_referee/correction_needed/rejected/recommend_publish
    feedback = Column(Text, nullable=False)
    score = Column(Integer, default=0, nullable=False)
    suggested_knowledge_code = Column(String, nullable=True)

    reviewed_ts = Column(Float, nullable=True)
    created_ts = Column(Float, nullable=False)

    submission = relationship("Submission", back_populates="assignments")

class SubmissionLike(Base):
    __tablename__ = "submission_likes"
    submission_id = Column(String, ForeignKey("submissions.id", ondelete="CASCADE"), primary_key=True)
    user_phone = Column(String, primary_key=True)
    created_ts = Column(Float, nullable=False)

    submission = relationship("Submission", back_populates="likes_rel")
    __table_args__ = (UniqueConstraint("submission_id", "user_phone", name="uq_like"),)

class SubmissionComment(Base):
    __tablename__ = "submission_comments"
    id = Column(String, primary_key=True)
    submission_id = Column(String, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    user_name = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    created_ts = Column(Float, nullable=False)

    submission = relationship("Submission", back_populates="comments")

class ForumPost(Base):
    __tablename__ = "forum_posts"
    id = Column(String, primary_key=True)
    sender_phone = Column(String, nullable=False)
    sender_name = Column(String, nullable=False)
    sender_role = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    status = Column(String, nullable=False)  # ForumStatus
    created_ts = Column(Float, nullable=False)

class ForumReply(Base):
    __tablename__ = "forum_replies"
    id = Column(String, primary_key=True)
    post_id = Column(String, ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False)
    referee_phone = Column(String, nullable=False)
    referee_name = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    created_ts = Column(Float, nullable=False)
