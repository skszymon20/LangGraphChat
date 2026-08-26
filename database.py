from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

Path("data").mkdir(exist_ok=True)

DATABASE_URL = "sqlite:///data/chatbot_memory.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Conversations(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, index=True, unique=True)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatMessages(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, index=True)
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class LongTermMemory(Base):
    __tablename__ = "long_term_memory"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, index=True)
    memory = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_database():
    Base.metadata.create_all(bind=engine)

def create_or_update_conversation(thread_id: str, first_message: str | None = None):
    session = session_local()
    try:
        conversation = session.query(Conversations).filter_by(thread_id=thread_id).first()
        if conversation:
            # conversation.updated_at = datetime.utcnow()
            pass
        else:
            title = "New Chat"
            if first_message:
                title = first_message.strip()[:50]  # Use the first message as the title, truncated to 50 characters
                if len(first_message.strip()) > 50:
                    title += "..."  # Add ellipsis if the title is truncated
            conversations = Conversations(thread_id=thread_id, title=title, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
            session.add(conversations)
        session.commit()
        session.close()
    except Exception as e:
        session.rollback()
        session.close()
        raise e

def list_conversations():
    session = session_local()
    try:
        conversations = session.query(Conversations).order_by(Conversations.updated_at.desc()).all()
        session.close()
        return conversations
    except Exception as e:
        session.rollback()
        session.close()
        raise e

def save_chat_message(thread_id: str, role: str, content: str):
    session = session_local()
    try:
        chat_message = ChatMessages(thread_id=thread_id, role=role, content=content, created_at=datetime.utcnow())
        session.add(chat_message)
        session.commit()
        session.close()
    except Exception as e:
        session.rollback()
        session.close()
        raise e

def get_chat_history(thread_id: str):
    session = session_local()
    try:
        chat_history = session.query(ChatMessages).filter_by(thread_id=thread_id).order_by(ChatMessages.created_at.asc()).all()
        session.close()
        return chat_history
    except Exception as e:
        session.rollback()
        session.close()
        raise e

def save_long_term_memory(thread_id: str, memory: str):
    session = session_local()
    try:
        long_term_memory = LongTermMemory(thread_id=thread_id, memory=memory, created_at=datetime.utcnow())
        session.add(long_term_memory)
        session.commit()
        session.close()
    except Exception as e:
        session.rollback()
        session.close()
        raise e

def search_long_term_memory(thread_id: str):
    session = session_local()
    try:
        long_term_memories = session.query(LongTermMemory).filter_by(thread_id=thread_id).order_by(LongTermMemory.created_at.asc()).limit(20).all()
        session.close()
        if not long_term_memories:
            return "There is no long-term memory for this thread."
        return '\n\n'.join([memory.memory for memory in long_term_memories])
    except Exception as e:
        session.rollback()
        session.close()
        raise e
