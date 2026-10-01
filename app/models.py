from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def now(): return datetime.now(timezone.utc)

class Message(Base):
    __tablename__="messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_chat_id: Mapped[str] = mapped_column(String(128))
    source_message_id: Mapped[int] = mapped_column(Integer)
    media_group_id: Mapped[str|None] = mapped_column(String(128), nullable=True)
    kind: Mapped[str] = mapped_column(String(32))
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__=(UniqueConstraint("source_chat_id","source_message_id",name="uq_source_message"),)

class Delivery(Base):
    __tablename__="deliveries"
    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(Integer, index=True)
    destination: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    remote_message_id: Mapped[str|None] = mapped_column(String(256), nullable=True)
    last_error: Mapped[str|None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    __table_args__=(UniqueConstraint("message_id","destination",name="uq_delivery"),)
