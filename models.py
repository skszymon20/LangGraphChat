from datetime import UTC, datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Thread(Base):
    __tablename__ = "threads"

    # NOTE removed auto id which was int.
    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)  # NOTE 36 - it is uuid. Might be other.
    title: Mapped[str] = mapped_column(String(53), nullable=False)  # NOTE 53 - it is 50 + 3 for ellipsis if title is truncated.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    messages: Mapped[list[Message]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )
    long_term_memories: Mapped[list[LongTermMemory]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )
    rag_files: Mapped[list[RAGFile]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("threads.id"), index=True)
    role: Mapped[str] = mapped_column(String(9))  # NOTE len('assistant'). Probably either 'user' or 'assistant'.
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    thread: Mapped[Thread] = relationship(back_populates="messages")
    tool_invocations: Mapped[list[ToolInvocation]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )

class ToolInvocation(Base):
    __tablename__ = "tools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("messages.id"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    arguments: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    result: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    message: Mapped[Message] = relationship(back_populates="tool_invocations")

class LongTermMemory(Base):
    __tablename__ = "long_term_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("threads.id"), index=True)
    memory: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    thread: Mapped[Thread] = relationship(back_populates="long_term_memories")

class RAGFile(Base):
    __tablename__ = "rag_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)  # NOTE 255 - it is a common max length for file names.
    added_to_vector_storage: Mapped[bool] = mapped_column(default=False)
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("threads.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    thread: Mapped[Thread] = relationship(back_populates="rag_files")

    @property
    def file_path(self) -> str:
        return f"data/rag_files/{self.file_name}"