from datetime import UTC, datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base



class Threads(Base):
    __tablename__ = "threads"

    # NOTE removed auto id which was int.
    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)  # NOTE 36 - it is uuid. Might be other.
    title: Mapped[str] = mapped_column(String(53), nullable=False)  # NOTE 53 - it is 50 + 3 for ellipsis if title is truncated.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    messages: Mapped[list[Messages]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )
    long_term_memories: Mapped[list[LongTermMemories]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )
    rag_files: Mapped[list[RAGFiles]] = relationship(
        back_populates="thread", cascade="all, delete-orphan"
    )

class Messages(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("threads.id"), index=True)
    role: Mapped[str] = mapped_column(String(9))  # NOTE len('assistant'). Probably either 'user' or 'assistant'.
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    thread: Mapped[Threads] = relationship(back_populates="messages")

class LongTermMemories(Base):
    __tablename__ = "long_term_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("threads.id"), index=True)
    memory: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    thread: Mapped[Threads] = relationship(back_populates="long_term_memories")

class RAGFiles(Base):
    __tablename__ = "rag_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)  # NOTE 255 - it is a common max length for file names.
    added_to_vector_storage: Mapped[bool] = mapped_column(default=False)
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("threads.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    thread: Mapped[Threads] = relationship(back_populates="rag_files")

    @property
    def file_path(self) -> str:
        return f"data/rag_files/{self.file_name}"