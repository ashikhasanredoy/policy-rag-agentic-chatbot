from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="EMPLOYEE", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan", lazy="selectin")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    category = Column(String(100), index=True, nullable=False)
    department = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    current_version = Column(String(50), default="1.0", nullable=False)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    versions = relationship("PolicyVersion", back_populates="policy", cascade="all, delete-orphan", lazy="selectin")


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, default=0)
    effective_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expiry_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="active", nullable=False)
    changelog = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    policy = relationship("Policy", back_populates="versions", lazy="selectin")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), default="New Conversation")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="conversations", lazy="selectin")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", lazy="selectin")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(100), primary_key=True, index=True)
    conversation_id = Column(String(100), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    answerable = Column(Boolean, default=True)
    confidence = Column(Float, default=1.0)
    sources = Column(JSON, default=list)
    latency_ms = Column(Float, default=0.0)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages", lazy="selectin")
    retrieval_log = relationship("RetrievalLog", back_populates="message", uselist=False, cascade="all, delete-orphan", lazy="selectin")


class RetrievalLog(Base):
    __tablename__ = "retrieval_logs"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(100), ForeignKey("messages.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(Integer, nullable=True)
    query = Column(Text, nullable=False)
    rewritten_query = Column(Text, nullable=True)
    retrieved_chunks_count = Column(Integer, default=0)
    reranked_chunks_count = Column(Integer, default=0)
    relevance_score = Column(Float, default=0.0)
    answerability_score = Column(Float, default=0.0)
    faithfulness_score = Column(Float, default=0.0)
    status = Column(String(50), default="answered")
    execution_trace = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    message = relationship("Message", back_populates="retrieval_log", lazy="selectin")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(100), nullable=False)
    user_id = Column(Integer, nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
